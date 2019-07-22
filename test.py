from flask import Flask
app=Flask(__name__)

@app.route('/index/') 
def index():
    return "hello world"

if __name__ == '__main__':
    print(__name__)
    app.debug=False
    app.run(host='localhost', port=5000)