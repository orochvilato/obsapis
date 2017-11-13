from obsapis import app
from flask import render_template

@app.route('/test')
def test():
    return render_template('svg/circofrance.svg', test="youpu")

if __name__ == "__main__":
    app.run()
