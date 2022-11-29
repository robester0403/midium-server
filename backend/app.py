#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import desc
from waitress import serve
from dotenv import load_dotenv
from pathlib import Path
import asyncio
import openai
import os


#----------------------------------------------------------------------------#
# Environment Setup
#----------------------------------------------------------------------------#

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:123456@localhost/alchemy"
db = SQLAlchemy(app)
CORS(app)
#----------------------------------------------------------------------------#
# OpenAI.
#----------------------------------------------------------------------------#
OPENAI_KEY = os.getenv('OPENAI_KEY')
openai.api_key = OPENAI_KEY
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
class User(db.Model):
  __tablename__ = 'users'
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)

  def __repr__(self): #representation
      return '<User %r>' % self.username
    
class Blogpost(db.Model):
  __tablename__ = 'blogposts'
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(80), unique=True, nullable=False)
  author = db.Column(db.String(80), nullable=False)
  content = db.Column(db.Text, nullable=False)
  created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  edited_at = db.Column(db.DateTime, nullable=True)

  def __repr__(self):
    return f'Blogpost: {self.title}' # F allows string interpolation of python variables

  def __init__(self, title, author, content): # constructor to create an object fromn a class
    self.title = title
    self.author = author
    self.content = content

def format_blogpost(blogpost): # formatted JSON object that can be returned without another network request
  return {
    'title': blogpost.title,
    'author': blogpost.author,
    'content': blogpost.content
  }

#----------------------------------------------------------------------------#
# Routes & Controllers.
#----------------------------------------------------------------------------#
@app.route('/api/aitest', methods=['GET'])
def hello_test():
  prompt = 'Write a point by point outline for a blog post that shows off to the general public what you learned to do today using javascript and React. The blog post should be more than 3 paragraphs and have lots of detail.The blog should be impressive to potential employers.. The tone of the blog post should be positive, humble and excited. Mention the accomplishment was in how you used Redux. Mention that redux may not always be the right choice in a full stack app. Mention any alternatives to Redux. Mention how you will continually work to get better.'
  response = openai.Completion.create(engine='text-davinci-002', prompt=prompt, max_tokens=300, temperature=0.6, top_p=1, frequency_penalty=0, presence_penalty=0.6)
  return response

@app.route('/api/aitextgenerate', methods=['POST'])
def generate_draftpost():
  language = request.json['language']
  framework = request.json['framework']
  prompt = request.json['prompt']
  # we will pass the prompts into the ai create function
  prompt = f'Write a 3 paragraph blog post that shows off to the general public what you learned to do today using {language} and {framework}. The blog post should be more than 3 paragraphs and have lots of detail.The blog should be impressive to potential employers. The tone of the blog post should be positive, humble and excited. {prompt} Mention how you will continually work to get better. Use some emojis.'

  result = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=100, temperature=0.9, top_p=1, frequency_penalty=0, presence_penalty=0.6)
  # loop = asyncio.get_event_loop()
  # result = loop.run_until_complete(openai.Completion.create(engine='text-davinci-002', prompt=prompt, max_tokens=100, temperature=0.9, top_p=1, frequency_penalty=0, presence_penalty=0.6))
  return result

  
@app.route('/api/aitextgenerate', methods=['POST'])
def generate():  asyncio.run(generate_draftpost())


# routes: Blogpost
@app.route('/api/blogpost', methods=['GET'])
def get_allposts():
  blogposts = Blogpost.query.order_by(desc(Blogpost.created_at)).all()
  if not blogposts or len(blogposts) == 0:
    return jsonify({'message': 'No blogposts found'})
  data = []
  for blogpost in blogposts:
    blogpost_data = {}
    # construct the object
    blogpost_data['title'] = blogpost.title
    blogpost_data['author'] = blogpost.author
    blogpost_data['content'] = blogpost.content
    blogpost_data['created_at'] = blogpost.created_at
    blogpost_data['edited_at'] = blogpost.edited_at
    data.append(blogpost_data)
  return jsonify({'posts': data})

@app.route('/api/blogpost/<blog_id>', methods = ['GET'])
def get_post(blog_id): # pass in the id here
  blogpost = Blogpost.query.filter_by(id=blog_id).first()
  if not blogpost:
    return jsonify({'message': 'No blog post of this id was found'})
  blogpost_data = {}
  blogpost_data['title'] = blogpost.title
  blogpost_data['author'] = blogpost.author
  blogpost_data['content'] = blogpost.content
  blogpost_data['created_at'] = blogpost.created_at
  blogpost_data['edited_at'] = blogpost.edited_at
  return jsonify({"data": blogpost_data})
  

@app.route('/api/blogpost', methods=['POST'])
def create_post():
  title = request.json['title']
  author = request.json['author']
  content = request.json['content']

  blogpost = Blogpost(title, author, content)

  db.session.add(blogpost)
  db.session.commit()

  return format_blogpost(blogpost) # returns info for the post created

@app.route('/api/blogpost/<blog_id>', methods=['PUT'])
def update_post(blog_id):
  blogpost = Blogpost.query.filter_by(id=blog_id).first()
  if not blogpost:
    return jsonify({'message': 'No blog post of this id was found'})
  title = request.json['title']
  author = request.json['author']
  content = request.json['content']

  blogpost.title = title
  blogpost.author = author
  blogpost.content = content
  blogpost.edited_at = datetime.utcnow()
  db.session.commit()
  
  return {'data': format_blogpost(blogpost)}

@app.route('/api/blogpost/<blog_id>', methods=['DELETE'])
def delete_post(blog_id):
  blogpost = Blogpost.query.filter_by(id=blog_id).first()
  if not blogpost:
    return jsonify({'message': 'No blog post of this id was found'})
  db.session.delete(blogpost)
  db.session.commit()
  return jsonify({'message': f'Blog post {blog_id} was deleted'})

# routes: Users
@app.route('/users', methods=['GET'])
def get_users():
  users = User.query.all()
  output = []
  for user in users:
      user_data = {}
      user_data['username'] = user.username
      user_data['email'] = user.email
      output.append(user_data)
  return jsonify({'users': output})

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
  user = User.query.filter_by(id=user_id).first()
  if not user:
      return jsonify({'message': 'No user found!'})
  user_data = {}
  user_data['username'] = user.username
  user_data['email'] = user.email
  return jsonify({'user': user_data})

@app.route('/users', methods=['POST'])
def create_user():
  data = request.get_json()
  new_user = User(username=data['username'], email=data['email'])
  db.session.add(new_user)
  db.session.commit()
  # return jsonify({'message': 'New user created!'})
  return repr(new_user)

    
@app.route('/users/<user_id>', methods=['PUT'])
def promote_user(user_id):
  user = User.query.filter_by(id=user_id).first()
  if not user:
      return jsonify({'message': 'No user found!'})
  user.admin = True
  db.session.commit()
  return jsonify({'message': 'The user has been promoted!'})

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
  user = User.query.filter_by(id=user_id).first()
  if not user:
      return jsonify({'message': 'No user found!'})
  db.session.delete(user)
  db.session.commit()
  return jsonify({'message': 'The user has been deleted!'})

# Python terminal command doesn't work so hardcode the table creation here
# with app.app_context():
#     db.create_all()

mode = 'dev'

#----------------------------------------------------------------------------#
# Dev vs Prod server
#----------------------------------------------------------------------------#

if __name__ == '__main__':
  if mode == 'dev':
    app.run( host='0.0.0.0', port=5000, debug=True )
  if mode == 'prod':
    serve(app, host='0.0.0.0', port=5000, threads=2)

