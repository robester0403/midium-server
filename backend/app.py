#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import desc
from waitress import serve

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:123456@localhost/alchemy"
db = SQLAlchemy(app)

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Hello this is a new instance?'})


# tables model
class User(db.Model):
  __tablename__ = 'users'
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)

  def __repr__(self): #representation
      return '<User %r>' % self.username
    
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
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
# Controllers.
#----------------------------------------------------------------------------#
@app.route('/tester', methods=['GET'])
def hello_test():
  return "Hello World!"

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
  return jsonify({'data': data})

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

if __name__ == '__main__':
  if mode == 'dev':
    app.run( host='0.0.0.0', port=5000, debug=True )
  if mode == 'prod':
    serve(app, host='0.0.0.0', port=5000, threads=2)

