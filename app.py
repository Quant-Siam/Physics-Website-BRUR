from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "physics_brur_2026"

# Database Setup
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Models ---
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50)) 
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    blood_group = db.Column(db.String(10))
    designation = db.Column(db.String(100))
    field_interest = db.Column(db.String(200))
    position_work = db.Column(db.String(100))
    expertise = db.Column(db.String(200))
    student_id = db.Column(db.String(50), unique=True) # Unique ID Constraint
    reg_no = db.Column(db.String(50))          
    batch = db.Column(db.String(20))           
    area_interest = db.Column(db.String(200))
    research_links = db.Column(db.Text)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(50))
    link = db.Column(db.String(300))

class Research(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    authors = db.Column(db.String(200))
    publication_date = db.Column(db.String(50))
    journal = db.Column(db.String(200))
    paper_link = db.Column(db.String(300))

# --- Routes ---

@app.route('/')
def home():
    notices = Notice.query.order_by(Notice.id.desc()).limit(5).all()
    return render_template('index.html', notices=notices)

@app.route('/notices')
def all_notices():
    notices = Notice.query.order_by(Notice.id.desc()).all()
    return render_template('notices.html', notices=notices, title="All Notices")

@app.route('/research')
def research():
    # ডেটাবেস থেকে সব রিসার্চ পেপার নিয়ে আসা (নতুনটি আগে থাকবে)
    researches = Research.query.order_by(Research.id.desc()).all()
    return render_template('research_view.html', researches=researches)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == '1234':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash("Invalid Credentials", "danger")
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('logged_in'): 
        return redirect(url_for('login'))
    members = Member.query.order_by(Member.id.desc()).all()
    notices = Notice.query.order_by(Notice.id.desc()).all()
    researches = Research.query.order_by(Research.id.desc()).all()
    return render_template('admin.html', members=members, notices=notices, researches=researches)

@app.route('/add_member', methods=['POST'])
def add_member():
    if session.get('logged_in'):
        s_id = request.form.get('student_id')
        category = request.form.get('category')
        
        # ডুপ্লিকেট আইডি চেক
        if s_id and s_id.strip():
            existing = Member.query.filter_by(student_id=s_id.strip()).first()
            if existing:
                flash(f"Error: Student ID {s_id} already exists!", "danger")
                return redirect(url_for('admin'))

        links_list = request.form.getlist('links[]')
        joined_links = ",".join([l.strip() for l in links_list if l.strip()])
        
        new_m = Member(
            category=category, name=request.form.get('name'), email=request.form.get('email'),
            phone=request.form.get('phone'), blood_group=request.form.get('blood'),
            designation=request.form.get('designation'), field_interest=request.form.get('field_interest'),
            position_work=request.form.get('position'), expertise=request.form.get('expertise'),
            student_id=s_id.strip() if s_id else None, 
            reg_no=request.form.get('reg_no'), batch=request.form.get('batch'),
            area_interest=request.form.get('area_interest'), research_links=joined_links
        )
        db.session.add(new_m)
        db.session.commit()
        flash("Member added successfully!", "success")
    return redirect(url_for('admin'))

@app.route('/add_notice', methods=['POST'])
def add_notice():
    if session.get('logged_in'):
        new_n = Notice(title=request.form.get('title'), date=request.form.get('date'), link=request.form.get('link'))
        db.session.add(new_n)
        db.session.commit()
        flash("Notice added successfully!", "success")
    return redirect(url_for('admin'))

@app.route('/add_research', methods=['POST'])
def add_research():
    if session.get('logged_in'):
        new_r = Research(
            title=request.form.get('title'), authors=request.form.get('authors'),
            publication_date=request.form.get('date'), journal=request.form.get('journal'),
            paper_link=request.form.get('link')
        )
        db.session.add(new_r)
        db.session.commit()
        flash("Research paper added successfully!", "success")
    return redirect(url_for('admin'))

@app.route('/delete_member/<int:id>')
def delete_member(id):
    if session.get('logged_in'):
        m = Member.query.get(id); db.session.delete(m); db.session.commit()
    return redirect(url_for('admin'))

@app.route('/delete_notice/<int:id>')
def delete_notice(id):
    if session.get('logged_in'):
        n = Notice.query.get(id); db.session.delete(n); db.session.commit()
    return redirect(url_for('admin'))

@app.route('/delete_research/<int:id>')
def delete_research(id):
    if session.get('logged_in'):
        r = Research.query.get(id); db.session.delete(r); db.session.commit()
    return redirect(url_for('admin'))

@app.route('/explore/<type>')
def explore(type):
    search_query = request.args.get('search')
    base_query = Member.query.filter_by(category=type).order_by(Member.student_id.asc())
    
    if search_query:
        data = base_query.filter(Member.student_id.contains(search_query)).all()
    else:
        data = base_query.all()

    if type in ['Student', 'Alumni']:
        batches = {}
        for m in data:
            b_name = m.batch if m.batch else "Unknown Batch"
            if b_name not in batches: batches[b_name] = []
            batches[b_name].append(m)
        
        sorted_batches = dict(sorted(batches.items(), key=lambda x: x[0], reverse=True))
        return render_template('view_section.html', batches=sorted_batches, title=type, is_batch=True)
    
    return render_template('view_section.html', members=data, title=type, is_batch=False)

@app.route('/member/<int:id>')
def member_details(id):
    m = Member.query.get_or_404(id)
    return render_template('details.html', m=m)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)