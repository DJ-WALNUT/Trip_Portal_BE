# routes/instagram_routes.py
from flask import Blueprint, jsonify
import requests
import os

insta_bp = Blueprint('instagram', __name__, url_prefix='/api/instagram')

@insta_bp.route('/posts', methods=['GET'])
def get_instagram_posts():
    # .env에서 토큰 가져오기
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    user_id = os.getenv('INSTAGRAM_USER_ID') # (선택) ID를 모르면 'me' 사용 가능
    
    # 1. 토큰이 없으면 더미 데이터 반환 (개발용)
    if not access_token:
        return jsonify({
            'status': 'success',
            'data': _get_dummy_posts()
        })

    try:
        # 2. 인스타그램 Graph API 호출
        # media_type, media_url, permalink, caption 필드 요청
        url = f"https://graph.instagram.com/me/media?fields=id,caption,media_type,media_url,thumbnail_url,permalink&access_token={access_token}&limit=7"
        
        res = requests.get(url)
        data = res.json()
        
        if 'error' in data:
            print("Instagram API Error:", data['error'])
            return jsonify({'status': 'success', 'data': _get_dummy_posts()})

        posts = []
        for item in data.get('data', []):
            # 동영상(VIDEO)인 경우 썸네일 사용, 아니면 이미지 URL 사용
            img_url = item.get('thumbnail_url') if item.get('media_type') == 'VIDEO' else item.get('media_url')
            
            posts.append({
                'id': item['id'],
                'imgUrl': img_url,
                'link': item.get('permalink', 'https://instagram.com'),
                'caption': item.get('caption', '')
            })
            
        return jsonify({'status': 'success', 'data': posts})

    except Exception as e:
        print("Server Error:", str(e))
        # 에러 나면 더미 데이터라도 보여줌
        return jsonify({'status': 'success', 'data': _get_dummy_posts()})

def _get_dummy_posts():
    """API 연동 전이나 에러 시 보여줄 임시 데이터"""
    return [
        { 'id': 1, 'color': '#3986c6', 'link': 'https://instagram.com', 'imgUrl': 'https://via.placeholder.com/600x600/3986c6/ffffff?text=Insta+1' },
        { 'id': 2, 'color': '#e74c3c', 'link': 'https://instagram.com', 'imgUrl': 'https://via.placeholder.com/600x600/e74c3c/ffffff?text=Insta+2' },
        { 'id': 3, 'color': '#2ecc71', 'link': 'https://instagram.com', 'imgUrl': 'https://via.placeholder.com/600x600/2ecc71/ffffff?text=Insta+3' },
        { 'id': 4, 'color': '#f1c40f', 'link': 'https://instagram.com', 'imgUrl': 'https://via.placeholder.com/600x600/f1c40f/ffffff?text=Insta+4' },
        { 'id': 5, 'color': '#9b59b6', 'link': 'https://instagram.com', 'imgUrl': 'https://via.placeholder.com/600x600/9b59b6/ffffff?text=Insta+5' },
        { 'id': 6, 'color': '#34495e', 'link': 'https://instagram.com', 'imgUrl': 'https://via.placeholder.com/600x600/34495e/ffffff?text=Insta+6' },
        { 'id': 7, 'color': '#95a5a6', 'link': 'https://instagram.com', 'imgUrl': 'https://via.placeholder.com/600x600/95a5a6/ffffff?text=Insta+7' },
    ]