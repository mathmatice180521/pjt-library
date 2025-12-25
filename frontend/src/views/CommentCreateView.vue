<template>
  <div class="comment-form-container">
    <h2>리뷰 작성</h2>
    <textarea v-model="content" placeholder="이 책에 대한 생각을 남겨주세요..."></textarea>
    <div class="actions">
      <button @click="$router.back()" class="btn-cancel">취소</button>
      <button @click="submitComment" :disabled="!content.trim() || store.isLoading" class="btn-submit">
        {{ store.isLoading ? '등록 중...' : '리뷰 등록' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useCommentsStore } from '@/stores/comments';

const props = defineProps(['bookId']);
const content = ref('');
const store = useCommentsStore();
const router = useRouter();

const submitComment = async () => {
  try {
    await store.createComment(props.bookId, content.value);
    alert('리뷰가 등록되었습니다.');
    router.push(`/books/${props.bookId}`);
  } catch (error) {
    alert('등록에 실패했습니다.');
  }
};
</script>

<style scoped>
.comment-form-container { max-width: 600px; margin: 50px auto; padding: 20px; }
textarea { width: 100%; height: 150px; padding: 15px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 20px; resize: none; }
.actions { display: flex; gap: 10px; justify-content: flex-end; }
.btn-submit { background: #ffeb00; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; cursor: pointer; }
.btn-cancel { background: #eee; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
</style>