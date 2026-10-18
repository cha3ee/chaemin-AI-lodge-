import os
import requests
import traceback
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Force load environment variables from .env file
load_dotenv(override=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'scrapbook-secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scrapbook.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure target upload directories exist safely
for subfolder in ['photos', 'voice', 'decorations']:
    target_path = os.path.join(UPLOAD_FOLDER, subfolder)
    if os.path.exists(target_path) and not os.path.isdir(target_path):
        os.remove(target_path)
    os.makedirs(target_path, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_username = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    is_favorited = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', backref='sent_notes')

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_username = db.Column(db.String(80), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255), nullable=True)
    is_anonymous = db.Column(db.Boolean, default=False)
    is_favorited = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', backref='sent_photos')

class VoiceMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_username = db.Column(db.String(80), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    is_anonymous = db.Column(db.Boolean, default=False)
    is_favorited = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', backref='sent_voices')

class BoardItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    item_type = db.Column(db.String(20), default='sticky')
    file_ref = db.Column(db.String(255), nullable=True)
    color = db.Column(db.String(20), default='yellow')
    pos_x = db.Column(db.Float, default=20.0)
    pos_y = db.Column(db.Float, default=20.0)
    rotation = db.Column(db.Float, default=0.0)
    scale = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials.')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    if request.method == 'POST':
        recipient = request.form.get('recipient', '').strip()
        content = request.form.get('content', '').strip()
        is_anonymous = 'is_anonymous' in request.form

        recipient_user = User.query.filter_by(username=recipient).first()
        if not recipient_user:
            flash(f'User "{recipient}" does not exist!')
            return redirect(url_for('notes'))

        new_note = Note(
            sender_id=current_user.id,
            recipient_username=recipient,
            content=content,
            is_anonymous=is_anonymous
        )
        db.session.add(new_note)
        db.session.commit()
        flash('Note sent!')
        return redirect(url_for('notes'))

    received_notes = Note.query.filter_by(recipient_username=current_user.username).order_by(Note.created_at.desc()).all()
    today_str = datetime.now().strftime('%d %b %Y')
    return render_template('notes.html', notes=received_notes, today_str=today_str)

@app.route('/note/<int:note_id>')
@login_required
def view_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.recipient_username != current_user.username and note.sender_id != current_user.id:
        flash("You do not have permission to view this note.")
        return redirect(url_for('notes'))

    return render_template('view_note.html', note=note)

@app.route('/photos', methods=['GET', 'POST'])
@login_required
def photos():
    if request.method == 'POST':
        file = request.files.get('photo_file')
        recipient = request.form.get('recipient', '').strip() or current_user.username
        caption = request.form.get('caption', '').strip()
        is_anonymous = 'is_anonymous' in request.form

        if file and file.filename != '':
            timestamp = int(datetime.utcnow().timestamp())
            filename = secure_filename(f"{timestamp}_{file.filename}")
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'photos', filename)
            file.save(save_path)

            new_photo = Photo(
                sender_id=current_user.id,
                recipient_username=recipient,
                filename=filename,
                caption=caption,
                is_anonymous=is_anonymous
            )
            db.session.add(new_photo)
            db.session.commit()
            flash('Photo uploaded!')

        return redirect(url_for('photos'))

    photos_list = Photo.query.filter(
        (Photo.recipient_username == current_user.username) | (Photo.sender_id == current_user.id)
    ).order_by(Photo.created_at.desc()).all()

    return render_template('photos.html', photos=photos_list)

@app.route('/voice', methods=['GET', 'POST'])
@login_required
def voice():
    if request.method == 'POST':
        file = request.files.get('voice_file')
        recipient = request.form.get('recipient', '').strip() or current_user.username
        title = request.form.get('title', '').strip() or 'Voice Note'
        is_anonymous = 'is_anonymous' in request.form

        if file and file.filename != '':
            timestamp = int(datetime.utcnow().timestamp())
            filename = secure_filename(f"{timestamp}_{file.filename}")
            if not (filename.endswith('.webm') or filename.endswith('.mp3') or filename.endswith('.wav')):
                filename += '.webm'

            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'voice', filename)
            file.save(save_path)

            new_voice = VoiceMessage(
                sender_id=current_user.id,
                recipient_username=recipient,
                filename=filename,
                title=title,
                is_anonymous=is_anonymous
            )
            db.session.add(new_voice)
            db.session.commit()
            flash('Voice recording saved!')

        return redirect(url_for('voice'))

    voices_list = VoiceMessage.query.filter(
        (VoiceMessage.recipient_username == current_user.username) | (VoiceMessage.sender_id == current_user.id)
    ).order_by(VoiceMessage.created_at.desc()).all()

    return render_template('voice.html', voices=voices_list)

@app.route('/toggle_favorite/<string:item_type>/<int:item_id>', methods=['POST'])
@login_required
def toggle_favorite(item_type, item_id):
    if item_type == 'note':
        item = Note.query.get_or_404(item_id)
    elif item_type == 'photo':
        item = Photo.query.get_or_404(item_id)
    elif item_type == 'voice':
        item = VoiceMessage.query.get_or_404(item_id)
    else:
        return redirect(url_for('home'))

    item.is_favorited = not item.is_favorited
    db.session.commit()
    return redirect(request.referrer or url_for('home'))

@app.route('/board', methods=['GET', 'POST'])
@login_required
def board():
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        item_type = request.form.get('item_type', 'sticky')
        file_ref = request.form.get('file_ref', '')

        if content or file_ref:
            new_item = BoardItem(
                user_id=current_user.id,
                content=content,
                item_type=item_type,
                file_ref=file_ref
            )
            db.session.add(new_item)
            db.session.commit()

        return redirect(url_for('board'))

    user_board_items = BoardItem.query.filter_by(user_id=current_user.id).order_by(BoardItem.created_at.desc()).all()
    fav_notes = Note.query.filter_by(recipient_username=current_user.username, is_favorited=True).all()
    fav_photos = Photo.query.filter(
        (Photo.recipient_username == current_user.username) | (Photo.sender_id == current_user.id),
        Photo.is_favorited == True
    ).all()
    fav_voices = VoiceMessage.query.filter(
        (VoiceMessage.recipient_username == current_user.username) | (VoiceMessage.sender_id == current_user.id),
        VoiceMessage.is_favorited == True
    ).all()

    return render_template(
        'board.html',
        board_items=user_board_items,
        fav_notes=fav_notes,
        fav_photos=fav_photos,
        fav_voices=fav_voices
    )

@app.route('/generate_decoration', methods=['POST'])
@login_required
def generate_decoration():
    prompt_text = request.form.get('prompt', '').strip()
    if not prompt_text:
        flash('Please enter a description for your sticker!')
        return redirect(url_for('board'))

    timestamp = int(datetime.utcnow().timestamp())
    filename = f"ai_sticker_{timestamp}.png"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'decorations', filename)

    create_fallback_sticker(save_path, prompt_text)

    new_item = BoardItem(
        user_id=current_user.id,
        content=prompt_text,
        item_type='decoration',
        file_ref=filename,
        pos_x=100.0,
        pos_y=100.0
    )
    db.session.add(new_item)
    db.session.commit()
    return redirect(url_for('board'))

def create_fallback_sticker(target_path, label):
    from PIL import Image, ImageDraw
    img = Image.new('RGBA', (300, 300), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([20, 20, 280, 280], fill=(255, 240, 245, 255), outline=(230, 150, 170, 255), width=8)
    draw.text((80, 130), f"✨ {label[:12]}", fill=(70, 50, 40, 255))
    img.save(target_path)
    return target_path

@app.route('/delete_board_item/<int:item_id>', methods=['POST'])
@login_required
def delete_board_item(item_id):
    item = BoardItem.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

@app.route('/update_board_item_transform/<int:item_id>', methods=['POST'])
@login_required
def update_board_item_transform(item_id):
    item = BoardItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    data = request.get_json() or {}
    item.pos_x = float(data.get('x', item.pos_x))
    item.pos_y = float(data.get('y', item.pos_y))
    item.rotation = float(data.get('rotation', item.rotation))
    item.scale = float(data.get('scale', item.scale))
    db.session.commit()

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

    @app.template_filter('localdate')
def localdate_filter(value, format_string='%d %b %Y'):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    if hasattr(value, 'strftime'):
        return value.strftime(format_string)
    return str(value)