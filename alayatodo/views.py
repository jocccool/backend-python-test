import json
from math import ceil
from alayatodo import app
from flask import (
    g,
    redirect,
    render_template,
    request,
    session
    )

# pagination
PER_PAGE = 5
class Pagination(object):
    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or (num > self.page - left_current - 1 and num < self.page + right_current) or num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num



@app.route('/')
def home():
    with app.open_resource('../README.md', mode='r') as f:
        readme = "".join(l.decode('utf-8') for l in f)
        return render_template('index.html', readme=readme)


@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_POST():
    username = request.form.get('username')
    password = request.form.get('password')

    sql = "SELECT * FROM users WHERE username = '%s' AND password = '%s'";
    cur = g.db.execute(sql % (username, password))
    user = cur.fetchone()
    if user:
        session['user'] = dict(user)
        session['logged_in'] = True
        return redirect('/todo')

    return redirect('/login')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user', None)
    return redirect('/')


@app.route('/todo/', defaults={'page':1}, methods=['GET'])
@app.route('/todo/page/<int:page>', methods=['GET'])
def todos(page):
    if not session.get('logged_in'):
        return redirect('/login')
    cur = g.db.execute("SELECT * FROM todos WHERE user_id = '%s'" % session['user']['id'])
    todos = cur.fetchall()
    count = len(todos)
    if not todos and page != 1:
        abort(404)
    pagination = Pagination(page, PER_PAGE, count)
    return render_template('todos.html', pagination=pagination, todos=todos)


@app.route('/todo', methods=['POST'])
@app.route('/todo/', methods=['POST'])
def todos_POST():
    if not session.get('logged_in'):
        return redirect('/login')
    g.db.execute(
        "INSERT INTO todos (user_id, description) VALUES ('%s', '%s') "
        % (session['user']['id'], request.form.get('description', ''))
    )
    g.db.commit()
    return redirect('/todo/page/'+request.form.get('page', ''))


@app.route('/todo/<id>/<p>', methods=['POST'])
def todo_done(id, p):
    if not session.get('logged_in'):
        return redirect('/login')
    g.db.execute("UPDATE todos SET done='TRUE' WHERE id ='%s'" % id)
    g.db.commit()
    return redirect('/todo/page/'+p)


@app.route('/todo/del/<id>/<p>', methods=['POST'])
def todo_delete(id, p):
    if not session.get('logged_in'):
        return redirect('/login')
    g.db.execute("DELETE FROM todos WHERE id ='%s'" % id)
    g.db.commit()
    #return render_template('todos.html', pagination=pagination, todos=todos)
    return redirect('/todo/page/'+p)


@app.route('/todo/<id>/json', methods=['GET'])
def todo_json(id):
    if not session.get('logged_in'):
        return redirect('/login')
    cur = g.db.execute("SELECT * FROM todos WHERE id ='%s' AND user_id = '%s'" % (id, session['user']['id']))
    todo = cur.fetchone()
    if not todo:
        return redirect('/')
    data = [{'id': todo['id'], 'user_id': todo['user_id'], 'description': todo['description'], 'done': todo['done']}]
    result = json.dumps(data)
    return result


@app.route('/todo/<id>/<p>', methods=['GET'])
def todo_view(id, p):
    if not session.get('logged_in'):
        return redirect('/login')
    cur = g.db.execute("SELECT * FROM todos WHERE id ='%s' AND user_id = '%s'" % (id, session['user']['id']))
    todo = cur.fetchone()
    return render_template('todo.html', todo=todo, p=p)
