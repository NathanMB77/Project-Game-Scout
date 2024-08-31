import schedule
import time
import requests
from flask import Flask, request, jsonify, url_for, Blueprint, send_from_directory
from api.models import db, Users, MyGames
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

from werkzeug.security import generate_password_hash, check_password_hash
import re

api = Blueprint('api', __name__)

# Allow CORS requests to this API
CORS(api)

def validate_email(email):
    return re.match(r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$', email)

def validate_password(password):
    return (len(password) >= 8 and any(char.isdigit() for char in password)
            and any(char.isupper() for char in password) and
            any(char.islower() for char in password))

def validate_username(username):
    return re.match(r'^[a-zA-Z0-9]{3,}$', username)

@api.route('/signup', methods=['POST'])
def create_user():

    email = request.json.get('email')
    password = request.json.get('password')
    username = request.json.get('username')

    if len(email) == 0:
        return jsonify({'error': 'Email is required'}, 400)
    if len(password) == 0:
        return jsonify({'error': 'Password is required'}, 400)
    if len(username) == 0:
        return jsonify({'error': 'Username is required'}, 400)
    
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}, 400)
    if not validate_password(password):
        return jsonify({'error': 'Password does not meet criteria'}, 400)
    if not validate_username(username):
        return jsonify({'error': 'Invalid username format'}, 400)

    existing_email = Users.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({'error': 'Email already in use'}, 400)
    
    existing_username = Users.query.filter_by(username=username).first()
    if existing_username:
        return jsonify({'error': 'Username already in use'}, 400)
    
    hashed_password = generate_password_hash(password)
    new_user = Users(email=email, username=username, password=hashed_password, is_active=False)

    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=new_user.id)
    return jsonify(access_token=access_token, success=True), 200

@api.route('/login', methods=['POST'])
def authenticate_user():
    email = request.json.get('email')
    username = request.json.get('username')
    password = request.json.get('password')
    user_by_email = Users.query.filter_by(email=email).first()
    user_by_username = Users.query.filter_by(username=username).first()
    user = user_by_email if user_by_email else user_by_username
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}, 400)
    
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token, success=True), 200

@api.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = Users.query.get(current_user_id)
    user_games = MyGames.query.filter_by(user_id=current_user_id).all()
    return jsonify(user=user.serialize(), user_games=[game.serialize() for game in user_games]), 200

@api.route('/fetch_popular_games', methods=['GET'])
def fetch_popular_games():
    url = "https://api.igdb.com/v4/games"
    payload = "fields name, cover, rating, rating_count, first_release_date;\r\nwhere rating_count > 200 & first_release_date > 1641016861;\r\nsort rating desc;"
    headers = {
        'Client-ID': 'o2vtxnf4vau6e9hwsuhhyr2lw2btkw',
        'Authorization': 'Bearer 3vaolqmz547wr9duldkw09vo2lkknn',
        'Content-Type': 'application/json',
        'Cookie': '__cf_bm=V8lg5oo1Wce.P0qaKsEq5Pn5ooZ6ScdRlZr9BYUN.Lw-1719431149-1.0.1.1-QMXeuEauQdEr1Dm3kZ1bcgQ_jNZCO9kI9_T.u.GB1Y.__dOuimKseZdlPuJynzA97_xmnothzBGhCnj6HMgrWw'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.json())
    ids = ""
    for game in response.json():
        print('aaaaaaaa')
        print(game)
        ids += str(game['cover']) + ','
    ids = ids[:-1]

    url = "https://api.igdb.com/v4/covers"
    payload = "fields id, image_id;\r\nwhere id = ("+ ids +");"
    response2 = requests.request("POST", url, headers=headers, data=payload)
    games = []
    for game in response.json():
        for cover in response2.json():
            if game['cover'] == cover['id']:
                game['image_id'] = cover['image_id']
                games.append(game)
                break

    return jsonify(games), 200

@api.route('/search', methods=['POST'])
def search():
    url = "https://api.igdb.com/v4/games"
    searchTerm = request.json.get('searchTerm')
    payload = "fields name, cover, rating, rating_count, first_release_date;\r\nsearch \"" + searchTerm + "\";\r\nwhere cover != null & version_parent = null & parent_game = null;\r\nlimit 50;"
    headers = {
        'Client-ID': 'o2vtxnf4vau6e9hwsuhhyr2lw2btkw',
        'Authorization': 'Bearer 3vaolqmz547wr9duldkw09vo2lkknn',
        'Content-Type': 'application/json',
        'Cookie': '__cf_bm=V8lg5oo1Wce.P0qaKsEq5Pn5ooZ6ScdRlZr9BYUN.Lw-1719431149-1.0.1.1-QMXeuEauQdEr1Dm3kZ1bcgQ_jNZCO9kI9_T.u.GB1Y.__dOuimKseZdlPuJynzA97_xmnothzBGhCnj6HMgrWw'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    ids = ""
    for game in response.json():
        ids += str(game['cover']) + ','
    ids = ids[:-1]

    url = "https://api.igdb.com/v4/covers"
    payload = "fields id, image_id;\r\nwhere id = ("+ ids +");"
    response2 = requests.request("POST", url, headers=headers, data=payload)

    games = []
    for game in response.json():
        for cover in response2.json():
            if game['cover'] == cover['id']:
                game['image_id'] = cover['image_id']
                games.append(game)
                break

    return jsonify(games), 200

@api.route('/fetch_game/<int:game_id>', methods=['GET'])
def fetch_game(game_id):
    url = "https://api.igdb.com/v4/games"
    payload = "fields name, rating, rating_count, first_release_date, summary, genres, platforms, screenshots;\r\nwhere id = " + str(game_id) + ";"
    headers = {
        'Client-ID': 'o2vtxnf4vau6e9hwsuhhyr2lw2btkw',
        'Authorization': 'Bearer 3vaolqmz547wr9duldkw09vo2lkknn',
        'Content-Type': 'application/json',
        'Cookie': '__cf_bm=V8lg5oo1Wce.P0qaKsEq5Pn5ooZ6ScdRlZr9BYUN.Lw-1719431149-1.0.1.1-QMXeuEauQdEr1Dm3kZ1bcgQ_jNZCO9kI9_T.u.GB1Y.__dOuimKseZdlPuJynzA97_xmnothzBGhCnj6HMgrWw'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    url = "https://api.igdb.com/v4/covers"
    payload = "fields image_id;\r\nwhere game = ("+ str(game_id) +");"
    # headers are the same as above, won't override
    response2 = requests.request("POST", url, headers=headers, data=payload)

    url = "https://api.igdb.com/v4/artworks"
    payload = "fields image_id;\r\nwhere game = "+ str(game_id) +";"
    # headers are the same as above, won't override
    response3 = requests.request("POST", url, headers=headers, data=payload)
    url = "https://api.igdb.com/v4/screenshots"
    payload = "fields image_id;\r\nwhere game = "+ str(game_id) +";"
    # headers are the same as above, won't override
    response4 = requests.request("POST", url, headers=headers, data=payload)
    game = response.json()[0]
    game['cover_id'] = response2.json()[0]['image_id']
    game['artworks'] = response3.json()
    game['screenshots'] = response4.json()

    return jsonify(game), 200

@api.route('review', methods=['POST'])
def review_game():
    user_id = request.json.get('user_id')
    game_id = request.json.get('game_id')
    cover_id = request.json.get('cover_id')
    rating = request.json.get('rating')
    review = request.json.get('review')
    liked = request.json.get('liked')

    existing_review = MyGames.query.filter_by(user_id=user_id, game_id=game_id).first()
    if existing_review:
        existing_review.rating = rating
        existing_review.review = review
        existing_review.liked = liked
        existing_review.cover_id = cover_id
        db.session.commit()
        return jsonify(existing_review.serialize()), 200
    else:
        new_review = MyGames(user_id=user_id, game_id=game_id, rating=rating, review=review, liked=liked, cover_id=cover_id)
        db.session.add(new_review)
        db.session.commit()
    return jsonify(new_review.serialize()), 200

@api.route('/search_users', methods=['POST'])
def search_users():
    search_term = request.json.get('searchTerm')
    users = Users.query.filter(Users.username.ilike(f'%{search_term}%')).all()
    return jsonify([user.serialize() for user in users]), 200

@api.route('/fetch_different_user/<username>', methods=['GET'])
def fetch_different_user(username):
    user = Users.query.filter_by(username=username).first()
    user_games = MyGames.query.filter_by(user_id=user.id).all()
    return jsonify(user=user.serialize(), user_games=[game.serialize() for game in user_games]), 200

@api.route('/follow', methods=['POST'])
def follow():
    follower_id = request.json.get('follower_id')
    followed_id = request.json.get('followed_id')
    follower = Users.query.get(follower_id)
    followed = Users.query.get(followed_id)

    if followed in follower.followed:
        return jsonify({'error': 'Already following this user'}), 400

    follower.followed.append(followed)
    db.session.commit()
    return jsonify(follower.serialize()), 200

@api.route('/unfollow', methods=['POST'])
def unfollow():
    follower_id = request.json.get('follower_id')
    followed_id = request.json.get('followed_id')
    follower = Users.query.get(follower_id)
    followed = Users.query.get(followed_id)
    if followed not in follower.followed:
        return jsonify({'error': 'Not following this user'}), 400
    follower.followed.remove(followed)
    db.session.commit()
    return jsonify(follower.serialize()), 200

@api.route('/fetch_all_reviews', methods=['GET'])
def fetch_all_reviews():
    reviews = MyGames.query.all()
    headers = {
        'Client-ID': 'o2vtxnf4vau6e9hwsuhhyr2lw2btkw',
        'Authorization': 'Bearer 3vaolqmz547wr9duldkw09vo2lkknn',
        'Content-Type': 'application/json',
        'Cookie': '__cf_bm=V8lg5oo1Wce.P0qaKsEq5Pn5ooZ6ScdRlZr9BYUN.Lw-1719431149-1.0.1.1-QMXeuEauQdEr1Dm3kZ1bcgQ_jNZCO9kI9_T.u.GB1Y.__dOuimKseZdlPuJynzA97_xmnothzBGhCnj6HMgrWw'
    }
    reviewList = []
    for review in reviews:
        review = review.serialize()
        review['username'] = Users.query.get(review['user_id']).username
        game_name = requests.request("POST", "https://api.igdb.com/v4/games", 
            headers=headers, 
            data="fields name; where id = " + str(review['game_id']) + ";")
        review['game_name'] = game_name.json()[0]['name']
        reviewList.append(review)
    return jsonify(reviewList), 200

@api.route('/fetch_user_reviews/<int:user_id>', methods=['GET'])
def fetch_user_reviews(user_id):
    reviews = MyGames.query.filter_by(user_id=user_id).all()
    headers = {
        'Client-ID': 'o2vtxnf4vau6e9hwsuhhyr2lw2btkw',
        'Authorization': 'Bearer 3vaolqmz547wr9duldkw09vo2lkknn',
        'Content-Type': 'application/json',
        'Cookie': '__cf_bm=V8lg5oo1Wce.P0qaKsEq5Pn5ooZ6ScdRlZr9BYUN.Lw-1719431149-1.0.1.1-QMXeuEauQdEr1Dm3kZ1bcgQ_jNZCO9kI9_T.u.GB1Y.__dOuimKseZdlPuJynzA97_xmnothzBGhCnj6HMgrWw'
    }
    reviewList = []
    for review in reviews:
        review = review.serialize()
        review['username'] = Users.query.get(review['user_id']).username
        game_name = requests.request("POST", "https://api.igdb.com/v4/games", 
            headers=headers, 
            data="fields name; where id = " + str(review['game_id']) + ";")
        review['game_name'] = game_name.json()[0]['name']
        reviewList.append(review)
    return jsonify(reviewList), 200

@api.route('/fetch_followed_users_reviews/<int:user_id>', methods=['GET'])
def fetch_followed_reviews(user_id):
    user = Users.query.get(user_id)
    headers = {
        'Client-ID': 'o2vtxnf4vau6e9hwsuhhyr2lw2btkw',
        'Authorization': 'Bearer 3vaolqmz547wr9duldkw09vo2lkknn',
        'Content-Type': 'application/json',
        'Cookie': '__cf_bm=V8lg5oo1Wce.P0qaKsEq5Pn5ooZ6ScdRlZr9BYUN.Lw-1719431149-1.0.1.1-QMXeuEauQdEr1Dm3kZ1bcgQ_jNZCO9kI9_T.u.GB1Y.__dOuimKseZdlPuJynzA97_xmnothzBGhCnj6HMgrWw'
    }
    followed_reviews = []
    for followed in user.followed:
        reviews = MyGames.query.filter_by(user_id=followed.id).all()
        for review in reviews:
            review = review.serialize()
            review['username'] = followed.username
            game_name = requests.request("POST", "https://api.igdb.com/v4/games", 
                headers=headers, 
                data="fields name; where id = " + str(review['game_id']) + ";")
            review['game_name'] = game_name.json()[0]['name']
            followed_reviews.append(review)
    return jsonify(followed_reviews), 200