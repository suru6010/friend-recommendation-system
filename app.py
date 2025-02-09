from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from collections import deque

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',  # Change if different
        password='Slushie3345',  # Set your password
        database='DAA'
    )

# Login Route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        
        connection.close()
        
        if user:
            session['user_id'] = user['user_id']
            return redirect(url_for('recommendations', user_id=user['user_id']))
        else:
            return 'Invalid credentials, please try again.'
    
    return render_template('login.html')


@app.route('/recommendations/<int:user_id>', methods=['GET'])
def recommendations(user_id):
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch all users and their friends to create adjacency list
    cursor.execute('SELECT * FROM friendships')
    friendships = cursor.fetchall()
    
    adj_list = {}
    for friendship in friendships:
        if friendship['user_id'] not in adj_list:
            adj_list[friendship['user_id']] = []
        if friendship['friend_id'] not in adj_list:
            adj_list[friendship['friend_id']] = []
        
        adj_list[friendship['user_id']].append(friendship['friend_id'])
        adj_list[friendship['friend_id']].append(friendship['user_id'])
    
    # Use BFS to find recommendations based on mutual friends
    recommendations = bfs(user_id, adj_list)
    
    # Fetch user names for recommendations
    recommendations_data = []
    for rec in recommendations:
        cursor.execute('SELECT name FROM users WHERE user_id = %s', (rec,))
        user_name = cursor.fetchone()['name']
        
        # Count mutual friends
        mutual_friends = len(set(adj_list[user_id]) & set(adj_list[rec]))
        
        # Only add users with at least one mutual friend
        if mutual_friends > 0:
         recommendations_data.append({
                'name': user_name,
                'mutual_friends': mutual_friends,
                'user_id': rec
            })
    recommendations_data = counting_sort_recommendations(recommendations_data)
    connection.close()
    
    return render_template('recommendations.html', recommendations=recommendations_data)

def bfs(user_id, adj_list):
    visited = set()
    queue = deque([user_id])
    visited.add(user_id)
    
    recommendations = set()
    
    while queue:
        current = queue.popleft()
        
        for friend in adj_list[current]:
            if friend not in visited:
                visited.add(friend)
                queue.append(friend)
                
                for mutual_friend in adj_list[friend]:
                    if mutual_friend != user_id and mutual_friend not in visited:
                     recommendations.add(mutual_friend)
    
    return recommendations

def counting_sort_recommendations(recommendations):
    # Find the maximum value of 'mutual_friends'
    max_mutual_friends = max(recommendations, key=lambda x: x['mutual_friends'])['mutual_friends']

    # Initialize count array
    count = [0] * (max_mutual_friends + 1)

    # Count occurrences of each mutual_friends value
    for rec in recommendations:
        count[rec['mutual_friends']] += 1

    # Accumulate counts (prefix sum)
    for i in range(1, len(count)):
        count[i] += count[i - 1]

    # Build the sorted output
    sorted_recommendations = [None] * len(recommendations)
    for rec in reversed(recommendations):  # Reverse to maintain stability
        mutual_friends = rec['mutual_friends']
        position = count[mutual_friends] - 1
        sorted_recommendations[position] = rec
        count[mutual_friends] -= 1

    # Reverse the list for descending order
    sorted_recommendations.reverse()
    return sorted_recommendations



# Add Friend Route
@app.route('/add_friend/<int:friend_id>', methods=['POST'])
def add_friend(friend_id):
    user_id = session.get('user_id')
    
    if user_id:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Insert the new friendship into the database
        cursor.execute('INSERT INTO friendships (user_id, friend_id) VALUES (%s, %s)', (user_id, friend_id))
        cursor.execute('INSERT INTO friendships (user_id, friend_id) VALUES (%s, %s)', (friend_id, user_id))
        
        connection.commit()
        connection.close()
        
        return redirect(url_for('recommendations', user_id=user_id))
    
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True) 
    
'''from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from collections import deque

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',  # Change if different
        password='Slushie3345',  # Set your password
        database='DAA'
    )

# Login Route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        
        connection.close()
        
        if user:
            session['user_id'] = user['user_id']
            return redirect(url_for('recommendations', user_id=user['user_id']))
        else:
            return 'Invalid credentials, please try again.'
    
    return render_template('login.html')

# Recommendations Route
@app.route('/recommendations/<int:user_id>', methods=['GET'])
def recommendations(user_id):
    # Create adjacency matrix from the friendships table
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch all users and their friendships
    cursor.execute('SELECT * FROM friendships')
    friendships = cursor.fetchall()
    
    # Find number of users (assuming user_ids are consecutive integers starting from 1)
    cursor.execute('SELECT COUNT(*) FROM users')
    num_users = cursor.fetchone()['COUNT(*)']
    
    # Create the adjacency matrix
    adj_matrix = [[0] * num_users for _ in range(num_users)]
    for friendship in friendships:
        u, v = friendship['user_id'] - 1, friendship['friend_id'] - 1
        adj_matrix[u][v] = 1
        adj_matrix[v][u] = 1  # Undirected graph

    # Perform matrix multiplication to compute mutual friends
    mutual_matrix = matrix_multiplication(adj_matrix)

    # Extract recommendations based on mutual friends
    recommendations_data = []
    for i in range(num_users):
        if i != (user_id - 1) and adj_matrix[user_id - 1][i] == 0 and mutual_matrix[user_id - 1][i] > 0:
            user_name = fetch_user_name(i + 1, cursor)
            mutual_friends = mutual_matrix[user_id - 1][i]
            recommendations_data.append({
                'name': user_name,
                'mutual_friends': mutual_friends,
                'user_id': i + 1
            })

    # Sort recommendations using counting sort
    recommendations_data = counting_sort_recommendations(recommendations_data)
    
    connection.close()
    return render_template('recommendations.html', recommendations=recommendations_data)

def matrix_multiplication(adj_matrix):
    num_users = len(adj_matrix)  # Get the number of users (the size of the matrix)
    mutual_matrix = [[0] * num_users for _ in range(num_users)]  # Initialize a matrix to store mutual friends
    
    # Perform matrix multiplication: A^2 = A * A, algo referenced from coreman
    for i in range(num_users):  
        for j in range(num_users): 
            for k in range(num_users): 
                mutual_matrix[i][j] += adj_matrix[i][k] * adj_matrix[k][j]
    
    return mutual_matrix

def fetch_user_name(user_id, cursor):
    cursor.execute('SELECT name FROM users WHERE user_id = %s', (user_id,))
    user_name = cursor.fetchone()['name']
    return user_name

def counting_sort_recommendations(recommendations):
    # Find the maximum value of 'mutual_friends'
    max_mutual_friends = max(recommendations, key=lambda x: x['mutual_friends'])['mutual_friends']

    # Initialize count array
    count = [0] * (max_mutual_friends + 1)

    # Count occurrences of each mutual_friends value
    for rec in recommendations:
        count[rec['mutual_friends']] += 1

    # Accumulate counts (prefix sum)
    for i in range(1, len(count)):
        count[i] += count[i - 1]

    # Build the sorted output
    sorted_recommendations = [None] * len(recommendations)
    for rec in reversed(recommendations):  # Reverse to maintain stability
        mutual_friends = rec['mutual_friends']
        position = count[mutual_friends] - 1
        sorted_recommendations[position] = rec
        count[mutual_friends] -= 1

    # Reverse the list for descending order
    sorted_recommendations.reverse()
    return sorted_recommendations

# Add Friend Route
@app.route('/add_friend/<int:friend_id>', methods=['POST'])
def add_friend(friend_id):
    user_id = session.get('user_id')
    
    if user_id:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Insert the new friendship into the database
        cursor.execute('INSERT INTO friendships (user_id, friend_id) VALUES (%s, %s)', (user_id, friend_id))
        cursor.execute('INSERT INTO friendships (user_id, friend_id) VALUES (%s, %s)', (friend_id, user_id))
        
        connection.commit()
        connection.close()
        
        return redirect(url_for('recommendations', user_id=user_id))
    
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True) '''

