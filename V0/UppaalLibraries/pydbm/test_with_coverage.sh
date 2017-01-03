python-coverage -e
python-coverage run test.py
python-coverage html -d coverage -i --omit=/usr/share
python-coverage report -i --omit=/usr/share
echo To view report in HTML, open coverage/index.html
