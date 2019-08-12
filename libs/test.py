from flask import Flask
app=Flask(__name__)

@app.route('/hello') 
def hello():
    return "hello world"

if __name__ == '__main__':
    #print(__name__)
    #app.debug=False
    app.run()