from flask import Flask, jsonify, request, render_template, redirect, url_for
from config import Config
from models import db, Stock, User
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database_name.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 設置 secret_key
app.secret_key = '$11009008'

# 初始化資料庫和登入管理
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 在應用程式上下文中創建所有表格
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 顯示股票投資組合
@app.route('/')
@login_required
def index():
    stocks = Stock.query.filter_by(user_id=current_user.id).all()
    return render_template('portfolio.html', portfolio=[stock.to_dict() for stock in stocks])

# 新增股票頁面
@app.route('/add_stock')
def add_stock_page():
    return render_template('add_stock.html')

# 單一股票詳情頁面
@app.route('/stock/<int:stock_id>')
def stock_detail(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    return render_template('stock_detail.html', stock=stock)

# 編輯股票頁面
@app.route('/edit_stock/<int:stock_id>')
def edit_stock_page(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    return render_template('edit_stock.html', stock=stock)

# API 1: 新增股票資料 (Create)
@app.route('/api/stocks', methods=['POST'])
@login_required
def create_stock():
    stock = Stock(
        stock=request.form['stock'],
        shares=int(request.form['shares']),
        bid_price=float(request.form['bid_price']),
        user_id=current_user.id
    )
    db.session.add(stock)
    db.session.commit()
    return redirect(url_for('index'))

# API 2: 查詢所有股票資料 (Read)
@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    stocks = Stock.query.all()
    return jsonify([stock.to_dict() for stock in stocks])

# API 3: 更新股票資料 (Update)
@app.route('/api/stocks/<int:id>', methods=['POST'])
@login_required
def update_stock(id):
    stock = Stock.query.get_or_404(id)
    if stock.owner != current_user:
        return "無權限編輯此股票", 403

    stock.stock = request.form['stock']
    stock.shares = int(request.form['shares'])
    stock.bid_price = float(request.form['bid_price'])
    db.session.commit()
    return redirect(url_for('index'))

# API 4: 刪除股票資料 (Delete)
@app.route('/stocks/<int:id>/delete', methods=['POST'])
@login_required
def delete_stock(id):
    stock = Stock.query.get_or_404(id)
    if stock.owner != current_user:
        return jsonify({"error": "無權限刪除此股票"}), 403
    db.session.delete(stock)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return "使用者已存在"
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        return "登入失敗"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
