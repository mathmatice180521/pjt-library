<template>
  <div class="comment-form-container">
    <h2>리뷰 수정</h2>
    <textarea 
      v-model="content" 
      placeholder="책에 대한 솔직한 생각을 남겨주세요."
    ></textarea>
    
    <div class="actions">
      <button @click="$router.back()" class="btn-cancel">취소</button>
      <button 
        @click="handleUpdate" 
        :disabled="!content.trim() || store.isLoading" 
        class="btn-submit"
      >
        {{ store.isLoading ? '수정 중...' : '수정 완료' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useCommentsStore } from '@/stores/comments';

const props = defineProps(['commentId']);
const store = useCommentsStore();
const router = useRouter();
const route = useRoute();

// 이전 페이지에서 쿼리로 받은 기존 내용을 초기값으로 설정
const content = ref(route.query.content || '');

const handleUpdate = async () => {
  if (!content.value.trim()) {
    alert('내용을 입력해주세요.');
    return;
  }
  try {
    await store.updateComment(props.commentId, content.value);
    alert('수정되었습니다.');
    router.back(); // 수정 후 이전 페이지(상세 페이지)로 돌아가기
  } catch (error) {
    alert('수정 실패: ' + (error.message || '알 수 없는 오류'));
  }
};
</script>

<style scoped>
/* CommentCreateView와 동일한 스타일 적용 */
.comment-form-container { 
  max-width: 600px; 
  margin: 50px auto; 
  padding: 20px; 
}

h2 {
  margin-bottom: 20px; /* 제목 아래 간격 추가 */
  color: #242424;
}

textarea { 
  width: 100%; 
  height: 150px; 
  padding: 15px; 
  border-radius: 8px; 
  border: 1px solid #ddd; 
  margin-bottom: 20px; 
  resize: none; 
  font-family: inherit; /* 폰트 상속 */
}

.actions { 
  display: flex; 
  gap: 10px; 
  justify-content: flex-end; 
}

.btn-submit { 
  background: #ffeb00; 
  border: none; 
  padding: 10px 20px; 
  border-radius: 5px; 
  font-weight: bold; 
  cursor: pointer; 
  color: #242424;
}

.btn-submit:disabled {
  background: #e0e0e0;
  cursor: not-allowed;
  color: #999;
}

.btn-cancel { 
  background: #eee; 
  border: none; 
  padding: 10px 20px; 
  border-radius: 5px; 
  cursor: pointer; 
}

.btn-cancel:hover {
  background: #e5e5e5;
}
</style>