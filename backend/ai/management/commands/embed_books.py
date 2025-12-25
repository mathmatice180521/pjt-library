import time
from typing import Dict, List

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from books.models import Book
from ai.models import BookEmbedding
from ai.utils import build_book_document_text, gemini_batch_embed_texts, vector_norm


class Command(BaseCommand):
    help = "Batch create/update BookEmbedding using Gemini batchEmbedContents."

    def add_arguments(self, parser):
        parser.add_argument("--batch", type=int, default=64)
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--start-id", type=int, default=0)
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--sleep", type=float, default=0.0)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        batch_size = max(1, int(opts["batch"]))
        force = bool(opts["force"])
        start_id = int(opts["start_id"])
        limit = int(opts["limit"])
        sleep_s = float(opts["sleep"])
        dry_run = bool(opts["dry_run"])

        embed_model = getattr(settings, "GEMINI_EMBED_MODEL", "text-embedding-004")
        api_key = getattr(settings, "GEMINI_API_KEY", "")
        if not api_key:
            self.stderr.write(self.style.ERROR("GEMINI_API_KEY가 settings에 없습니다."))
            return

        qs = Book.objects.all().order_by("id")
        if start_id > 0:
            qs = qs.filter(id__gte=start_id)
        if limit and limit > 0:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(self.style.SUCCESS(
            f"[embed_books] model={embed_model} batch={batch_size} force={force} total={total} dry_run={dry_run}"
        ))

        ok = skip = fail = 0
        t_all0 = time.time()

        idx = 0
        while idx < total:
            books = list(qs[idx: idx + batch_size])
            if not books:
                break

            try:
                existing: Dict[int, BookEmbedding] = {
                    be.book_id: be
                    for be in BookEmbedding.objects.filter(book__in=books)
                }

                targets: List[Book] = []
                texts: List[str] = []

                for b in books:
                    be = existing.get(b.id)
                    if (not force) and be and be.embedding and be.embedding_norm:
                        skip += 1
                        continue
                    targets.append(b)
                    texts.append(build_book_document_text(b))

                if not targets:
                    idx += batch_size
                    self.stdout.write(f"[{min(idx, total)}/{total}] all skipped | ok {ok} skip {skip} fail {fail}")
                    if sleep_s:
                        time.sleep(sleep_s)
                    continue

                t0 = time.time()
                vecs = gemini_batch_embed_texts(texts)
                dt = time.time() - t0

                if len(vecs) != len(targets):
                    raise RuntimeError(f"벡터 개수 불일치 got={len(vecs)} expected={len(targets)}")

                to_create: List[BookEmbedding] = []
                to_update: List[BookEmbedding] = []

                for b, v in zip(targets, vecs):
                    if not v:
                        fail += 1
                        continue

                    n = vector_norm(v)
                    be = existing.get(b.id)
                    if be is None:
                        to_create.append(BookEmbedding(
                            book=b,
                            embedding=v,
                            embedding_norm=n,
                            embedding_model=embed_model,
                        ))
                    else:
                        be.embedding = v
                        be.embedding_norm = n
                        be.embedding_model = embed_model
                        to_update.append(be)

                    ok += 1

                if not dry_run:
                    with transaction.atomic():
                        if to_create:
                            BookEmbedding.objects.bulk_create(to_create, batch_size=1000)
                        if to_update:
                            BookEmbedding.objects.bulk_update(
                                to_update,
                                ["embedding", "embedding_norm", "embedding_model"],
                                batch_size=1000
                            )

                idx += batch_size
                self.stdout.write(
                    f"[{min(idx, total)}/{total}] embedded {len(targets)} in {dt:.2f}s | ok {ok} skip {skip} fail {fail}"
                )

                if sleep_s:
                    time.sleep(sleep_s)

            except KeyboardInterrupt:
                self.stderr.write(self.style.WARNING("\n중단됨(CTRL+C). 지금까지 저장된 건 유지됩니다."))
                break

        total_dt = time.time() - t_all0
        self.stdout.write(self.style.SUCCESS(
            f"[DONE] ok={ok} skip={skip} fail={fail} elapsed={total_dt/60:.1f}min"
        ))
