<template>
  <Transition name="slide-up">
    <div v-if="isVisible" class="chat-modal-wrapper">
      <div class="chat-header">
        <div class="header-left">
          <span class="bot-icon">🤖</span>
          <span class="header-title">AI 도우미 웅성이</span>
        </div>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <div class="chat-body" ref="chatDisplay">
        <div v-for="(msg, index) in messages" :key="index" :class="['message-row', msg.sender]">
          <div v-if="msg.sender === 'ai'" class="profile-icon">🤖</div>
          <div class="message-content">
            <div v-if="msg.sender === 'ai'" class="sender-name">웅성이</div>
            <div class="bubble">
              <div v-if="msg.text" class="text-content">{{ msg.text }}</div>
              
              <div v-if="msg.books && msg.books.length > 0" class="book-list">
                <div v-for="book in msg.books" :key="book.book_pk" class="book-card-wrapper">
                    <div class="book-card" @click="goToDetail(book.book_pk)">
                        <img :src="resolveImageUrl(book.cover)" class="book-cover" />
                        <div class="book-info">
                            <div class="book-title">{{ book.title }}</div>
                            <div class="book-reason">{{ book.reason }}</div>
                        </div>
                    </div>
                    <button class="create-comic-btn" @click.stop="requestComic(book)">
                        🎨 이 책 4컷 만화 만들기
                    </button>
                </div>
              </div>

              <div v-if="msg.image" class="comic-preview-container">
                  <img :src="resolveImageUrl(msg.image)" class="chat-comic-img" alt="만화 미리보기" />
                  <p class="preview-caption">이미지가 생성되었습니다! 마이페이지에서 다운로드 가능해요.</p>
              </div>

            </div>
          </div>
        </div>

        <div v-if="aiStore.isLoading" class="message-row ai">
             <div class="profile-icon">🤖</div>
             <div class="message-content">
                <div class="sender-name">웅성이</div>
                <div class="bubble loading"><div class="dot-flashing"></div></div>
             </div>
        </div>
        <div v-if="aiStore.isGeneratingComic" class="message-row ai">
            <div class="profile-icon">🤖</div>
            <div class="message-content">
                <div class="sender-name">웅성이</div>
                <div class="bubble">열심히 그림을 그려보고 있어요... 🎨 (약 10초 소요)</div>
            </div>
        </div>

      </div>

      <div class="suggestion-chips">
        <button v-for="keyword in suggestionKeywords" :key="keyword" @click="selectKeyword(keyword)" class="chip">{{ keyword }}</button>
      </div>

      <div class="chat-footer">
        <textarea 
          v-model="userPrompt" 
          placeholder="주제나 줄거리를 입력하거나 위 키워드를 선택하세요."
          @keyup.enter.exact="sendMessage"
        ></textarea>
        <button class="send-btn" @click="sendMessage" :disabled="!userPrompt.trim() || aiStore.isLoading || aiStore.isGeneratingComic">
          전송
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAiStore } from '@/stores/airecommend';
import { useAccountsStore } from '@/stores/accounts';

const props = defineProps(['isVisible']);
const emit = defineEmits(['close']);

const router = useRouter();
const aiStore = useAiStore();
const accountsStore = useAccountsStore();

// [설정] API 주소
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

// [핵심 수정] 이미지 URL 보정 (도메인 추출 로직)
const resolveImageUrl = (url) => {
  if (!url) return '';
  if (url.startsWith('http')) return url;

  try {
    let domain = 'http://127.0.0.1:8000';
    if (API_BASE_URL.startsWith('http')) {
        const urlObj = new URL(API_BASE_URL);
        domain = urlObj.origin; 
    }
    const cleanPath = url.startsWith('/') ? url : `/${url}`;
    return `${domain}${cleanPath}`;
  } catch (e) {
    return url;
  }
};

const userPrompt = ref('');
const chatDisplay = ref(null);
const messages = ref([]);

const suggestionKeywords = [
  "진로/미래 고민", "힐링과 위로", "달달한 로맨스", 
  "흥미진진 추리/미스터리", "동기부여/자기계발", "인간관계 처세술",
  "역사/인문학 지식", "상상력 자극 판타지", "경제/재테크 공부",
  "맛있는 요리 이야기", "가벼운 여행 에세이", "IT/과학 트렌드"
];

onMounted(() => { resetChat(); });

watch(() => props.isVisible, (newVal) => {
  if (newVal) { scrollToBottom(); if (messages.value.length === 0) resetChat(); }
});

const resetChat = () => {
  const username = accountsStore.username || '회원';
  messages.value = [{ sender: 'ai', text: `안녕하세요 ${username}님! 👋\n어떤 책을 찾으시나요?\n직접 입력하시거나 아래 키워드를 눌러보세요!` }];
};

const selectKeyword = (keyword) => { userPrompt.value = `${keyword}에 관련된 책 추천해줘`; sendMessage(); };

const scrollToBottom = async () => { await nextTick(); if (chatDisplay.value) chatDisplay.value.scrollTop = chatDisplay.value.scrollHeight; };

const sendMessage = async () => {
  if (!userPrompt.value.trim() || aiStore.isLoading) return;

  const text = userPrompt.value;
  messages.value.push({ sender: 'user', text });
  userPrompt.value = '';
  scrollToBottom();

  try {
    const data = await aiStore.getRecommendation(text);
    messages.value.push({
      sender: 'ai',
      text: '회원님의 취향에 딱 맞는 책을 골라봤어요! 📚',
      books: data.recommended_list
    });
  } catch (error) {
    const errorMsg = error.message || '추천 중 오류가 발생했습니다.';
    messages.value.push({ sender: 'ai', text: `😥 ${errorMsg}` });
  } finally {
    scrollToBottom();
  }
};

const goToDetail = (id) => {
  emit('close'); 
  router.push(`/books/${id}`);
};

const requestComic = async (book) => {
    if (aiStore.isGeneratingComic) return; 

    messages.value.push({ 
        sender: 'user', 
        text: `"${book.title}" 4컷 만화 만들어줘!` 
    });
    scrollToBottom();

    try {
        const data = await aiStore.generateComic(book.book_pk);
        
        // 메시지에 이미지 URL을 담을 때도 그냥 경로만 담으면
        // 템플릿의 <img :src="resolveImageUrl(msg.image)"> 가 알아서 처리함
        messages.value.push({
            sender: 'ai',
            text: `"${book.title}"의 4컷 만화가 완성되었어요! 🎉\n\n이미지가 성공적으로 저장이 되었어요!\n마이페이지로 가시면 이미지를 다운받으실 수가 있습니다!`,
            image: data.comic_url 
        });
    } catch (error) {
        messages.value.push({ 
            sender: 'ai', 
            text: '죄송해요, 그림을 그리다가 실수를 했어요. 잠시 후 다시 시도해주세요. 😥' 
        });
    } finally {
        scrollToBottom();
    }
};
</script>

<style scoped>
/* CSS는 기존과 동일하게 유지 */
.chat-modal-wrapper { position: fixed; bottom: 30px; right: 30px; width: 380px; height: 600px; background: #fff; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); display: flex; flex-direction: column; z-index: 2000; overflow: hidden; border: 1px solid #eee; font-family: 'Pretendard', sans-serif; }
.chat-header { background: #ffeb00; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; font-weight: bold; color: #3b1e1e; }
.header-left { display: flex; align-items: center; gap: 8px; }
.bot-icon { font-size: 20px; }
.close-btn { background: none; border: none; font-size: 20px; cursor: pointer; color: #3b1e1e; }
.chat-body { flex: 1; background: #b2c7d9; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
.message-row { display: flex; width: 100%; }
.message-row.ai { justify-content: flex-start; }
.message-row.user { justify-content: flex-end; }
.profile-icon { width: 36px; height: 36px; background: #fff; border-radius: 40%; display: flex; align-items: center; justify-content: center; font-size: 20px; margin-right: 8px; border: 1px solid #ddd; }
.message-content { max-width: 80%; }
.sender-name { font-size: 12px; color: #555; margin-bottom: 4px; margin-left: 2px; }
.bubble { padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.5; word-break: break-word; white-space: pre-line; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
.ai .bubble { background: #fff; color: #242424; border-top-left-radius: 2px; }
.user .bubble { background: #ffeb00; color: #3b1e1e; border-top-right-radius: 2px; }
.book-list { display: flex; flex-direction: column; gap: 12px; margin-top: 10px; }
.book-card-wrapper { background: #f8f8f8; border-radius: 8px; border: 1px solid #eee; overflow: hidden; }
.book-card { display: flex; gap: 10px; padding: 10px; cursor: pointer; transition: 0.2s; }
.book-card:hover { background: #f0f0f0; }
.book-cover { width: 40px; height: 60px; object-fit: cover; border-radius: 4px; flex-shrink: 0; }
.book-info { display: flex; flex-direction: column; justify-content: center; overflow: hidden; }
.book-title { font-weight: bold; font-size: 13px; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.book-reason { font-size: 11px; color: #666; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.create-comic-btn { width: 100%; border: none; background: #eef1f4; color: #555; font-size: 11px; padding: 8px 0; cursor: pointer; border-top: 1px solid #eee; font-weight: bold; transition: 0.2s; }
.create-comic-btn:hover { background: #dfe4ea; color: #333; }
.comic-preview-container { margin-top: 10px; border-radius: 8px; overflow: hidden; }
.chat-comic-img { width: 100%; height: auto; display: block; border-radius: 8px; border: 1px solid #eee; }
.preview-caption { font-size: 12px; color: #888; margin-top: 5px; text-align: center; }
.suggestion-chips { background: #fff; padding: 10px 15px; display: flex; gap: 8px; overflow-x: auto; border-top: 1px solid #eee; scrollbar-width: none; }
.suggestion-chips::-webkit-scrollbar { display: none; }
.chip { flex-shrink: 0; background: #f1f2f4; border: 1px solid #ddd; padding: 6px 12px; border-radius: 20px; font-size: 12px; color: #555; cursor: pointer; transition: 0.2s; }
.chip:hover { background: #3b1e1e; color: #fff; border-color: #3b1e1e; }
.chat-footer { background: #fff; padding: 10px 15px; display: flex; gap: 10px; border-top: 1px solid #eee; }
textarea { flex: 1; height: 36px; border: 1px solid #ddd; border-radius: 18px; padding: 8px 15px; resize: none; outline: none; font-size: 14px; background: #f8f8f8; }
textarea:focus { background: #fff; border-color: #ffeb00; }
.send-btn { background: #ffeb00; color: #3b1e1e; border: none; padding: 0 15px; border-radius: 18px; font-weight: bold; font-size: 13px; cursor: pointer; }
.send-btn:disabled { background: #eee; color: #aaa; cursor: not-allowed; }
.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(20px); }
.dot-flashing { position: relative; width: 6px; height: 6px; border-radius: 5px; background-color: #999; animation: dot-flashing 1s infinite linear alternate; animation-delay: 0.5s; margin: 0 10px; }
.dot-flashing::before, .dot-flashing::after { content: ""; display: inline-block; position: absolute; top: 0; width: 6px; height: 6px; border-radius: 5px; background-color: #999; animation: dot-flashing 1s infinite alternate; }
.dot-flashing::before { left: -10px; animation-delay: 0s; }
.dot-flashing::after { left: 10px; animation-delay: 1s; }
@keyframes dot-flashing { 0% { background-color: #999; } 100% { background-color: #e0e0e0; } }
@media (max-width: 600px) { .chat-modal-wrapper { top: 0; left: 0; width: 100%; height: 100%; border-radius: 0; bottom: 0; right: 0; } }
</style>