import time
import datetime
import json
import requests
import urlparse
import ast
import pygal
from pygal.style import LightStyle

from collections import defaultdict, OrderedDict

from flask import Flask, jsonify, abort, make_response, render_template, request
from flask_restful import Api, Resource, reqparse, fields, marshal


app = Flask(__name__, static_url_path="")
api = Api(app)


@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Unauthorized access'}), 403

# holds all the test data sent
tests = []

# structure of the test data
test_fields = {
    'test_name': fields.String,
    'date': fields.String,
    'test_start_time': fields.String,
    'test_end_time': fields.String,
    'test_time_diff': fields.String,
    'errors': fields.String,
    'screenshots': fields.String,
    'tags': fields.String,
    'comments': fields.String,
}

# utilize parser to parse through the test data arriving
parser = reqparse.RequestParser()
parser.add_argument('test_name', required=True, help="Test Name cannot be null!")
parser.add_argument('date', type=str, location='json')
parser.add_argument('test_start_time', type=str, location='json')
parser.add_argument('test_end_time', type=str, location='json')
parser.add_argument('test_time_diff', type=str, location='json')
parser.add_argument('errors', type=str, location='json')
parser.add_argument('screenshots', type=str, location='json')
parser.add_argument('tags', type=str, location='json')
parser.add_argument('comments', type=str, location='json')


def abort_if_tests_doesnt_exist(test_name):
    if test_name not in tests:
        abort(404, "Test {} doesn't exist".format(test_name))


# checks if the test is present
def test_checker(test_name):
    test_data = [test for test in tests if test['test_name'] == test_name]
    test_info = sorted(test_data, key=lambda data: datetime.datetime.strptime(data['date'], '%Y-%m-%d (%H:%M hours)'), reverse=True)
    if len(test_info) == 0:
        abort(404, )
    else:
        return test_info


# checks if the tag is present
def tag_checker(tag_name):
    test_data = [test for test in tests if tag_name in test['tags']]
    test_info = sorted(test_data, key=lambda data: datetime.datetime.strptime(data['date'], '%Y-%m-%d (%H:%M hours)'), reverse=True)
    if len(test_info) == 0:
        abort(404, )
    else:
        return test_info


# checks for entire variation of data on search page
def data_checker(full_url_data):
    parsed = urlparse.urlparse(full_url_data).query
    parsed_dict = urlparse.parse_qs(parsed)

    if 'test_name' in parsed_dict and 'tags' in parsed_dict and 'time_greater_than' in parsed_dict and 'date' in parsed_dict:
        test_data = [test for test in tests if parsed_dict['tags'][0] in test['tags']
                     and parsed_dict['test_name'][0] in test['test_name']
                     and float(test['test_time_diff']) > float(parsed_dict['time_greater_than'][0])
                     and parsed_dict['date'][0] in test['date']]

    elif 'test_name' in parsed_dict and 'tags' in parsed_dict and 'time_greater_than' in parsed_dict:
        test_data = [test for test in tests if parsed_dict['tags'][0] in test['tags']
                     and parsed_dict['test_name'][0] in test['test_name']
                     and float(test['test_time_diff']) > float(parsed_dict['time_greater_than'][0])]

    elif 'test_name' in parsed_dict and 'tags' in parsed_dict and 'date' in parsed_dict:
        test_data = [test for test in tests if parsed_dict['tags'][0] in test['tags']
                     and parsed_dict['test_name'][0] in test['test_name']
                     and parsed_dict['date'][0] in test['date']]

    elif 'test_name' in parsed_dict and 'time_greater_than' in parsed_dict and 'date' in parsed_dict:
        test_data = [test for test in tests if float(test['test_time_diff']) > float(parsed_dict['time_greater_than'][0])
                     and parsed_dict['test_name'][0] in test['test_name']
                     and parsed_dict['date'][0] in test['date']]

    elif 'date' in parsed_dict and 'tags' in parsed_dict and 'time_greater_than' in parsed_dict:
        test_data = [test for test in tests if parsed_dict['tags'][0] in test['tags']
                     and parsed_dict['date'][0] in test['date']
                     and float(test['test_time_diff']) > float(parsed_dict['time_greater_than'][0])]

    elif 'test_name' in parsed_dict and 'tags' in parsed_dict:
        test_data = [test for test in tests if parsed_dict['tags'][0] in test['tags'] and parsed_dict['test_name'][0] in test['test_name']]

    elif 'test_name' in parsed_dict and 'time_greater_than' in parsed_dict:
        test_data = [test for test in tests if parsed_dict['test_name'][0] in test['test_name'] and float(test['test_time_diff']) > float(parsed_dict['time_greater_than'][0])]

    elif 'tags' in parsed_dict and 'time_greater_than' in parsed_dict:
        test_data = [test for test in tests if parsed_dict['tags'][0] in test['tags'] and float(test['test_time_diff']) > float(parsed_dict['time_greater_than'][0])]

    elif 'test_name' in parsed_dict:
        test_data = [test for test in tests if parsed_dict['test_name'][0] in test['test_name']]

    elif 'tags' in parsed_dict:
        test_data = [test for test in tests if parsed_dict['tags'][0] in test['tags']]

    elif 'date' in parsed_dict:
        test_data = [test for test in tests if parsed_dict['date'][0] in test['date']]

    elif 'time_greater_than' in parsed_dict:
        test_data = [test for test in tests if float(test['test_time_diff']) > float(parsed_dict['time_greater_than'][0])]

    else:
        test_data = []

    test_info = sorted(test_data, key=lambda data: datetime.datetime.strptime(data['date'], '%Y-%m-%d (%H:%M hours)'), reverse=True)
    return test_info


class TestData(Resource):
    def get(self, test_name):
        test_info = test_checker(test_name)
        return {'test_data': [marshal(test, test_fields) for test in test_info]}

    # def put(self, test_name):
    #     args = parser.parse_args()
    #     task = {'task': args['task']}
    #     todos[test_id] = task
    #     return task, 201

    # def delete(self, test_id):
    #     abort_if_tests_doesnt_exist(test_id)
    #     del todos[test_id]
    #     return {"msg": "successfully deleted"}, 204


class TagData(Resource):
    def get(self, tag_name):
        test_info = tag_checker(tag_name)
        return {'test_data': [marshal(test, test_fields) for test in test_info]}


class TestDataList(Resource):
    def get(self):
        return {'tests_data': [marshal(test, test_fields) for test in tests]}

    def post(self):
        args = parser.parse_args()
        test = {
                    "test_name": args['test_name'],
                    "date": args['date'],
                    "test_start_time": args['test_start_time'],
                    "test_end_time": args['test_end_time'],
                    "test_time_diff": args['test_time_diff'],
                    "errors": ast.literal_eval(args['errors']),
                    "screenshots": ast.literal_eval(args['screenshots']),
                    "tags": ast.literal_eval(args['tags']),
                    "comments": args['comments']
                }

        tests.append(test)
        return {'tests_data': marshal(test, test_fields)}, 201


api.add_resource(TestDataList, '/tests')
api.add_resource(TestData, '/tests/<test_name>')
api.add_resource(TagData, '/tags/<tag_name>')


@app.route('/analytics')
def analytics():

    line_chart = pygal.Line()
    line_chart.title = 'Errors found'
    line_chart.x_labels = map(str, [x["test_name"] for x in tests])
    line_chart.add('# of errors', [len(x["errors"]) for x in tests])
    line_c = line_chart.render(is_unicode=True)

    bar_chart = pygal.HorizontalStackedBar(style=LightStyle)
    bar_chart.title = "Remarquable sequences"
    bar_chart.x_labels = map(str, range(11))
    bar_chart.add('Fibonacci', [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55])
    bar_chart.add('Padovan', [1, 1, 1, 2, 2, 3, 4, 5, 7, 9, 12])
    bar_chart.add('Data', [len(x["errors"]) for x in tests])
    chart = bar_chart.render(is_unicode=True)

    s_bar_chart = pygal.Bar()
    s_bar_chart.title = "Errors found:"
    s_bar_chart.x_labels = map(str, [x["test_name"] for x in tests])
    s_bar_chart.add('# of Errors', [len(x["errors"]) for x in tests])
    s_chart = s_bar_chart.render(is_unicode=True)

    #####################################################################
    # XXX: sort the tests by date

    sorted_tests = sorted(tests, key=lambda data: datetime.datetime.strptime(data['date'], '%Y-%m-%d (%H:%M hours)'), reverse=True)

    #####################################################################
    # XXX: gathers all tests by date

    tests_by_d = defaultdict(list)
    for test in sorted_tests:
        tests_by_d[test['date']].append(test['test_name'])

    tests_by_date = OrderedDict(sorted(tests_by_d.items(), reverse=True))

    print tests_by_date

    #####################################################################
    # XXX: gathers all errors by date

    errors_by_d = defaultdict(list)
    for test in sorted_tests:
        errors_by_d[test['date']].append(test['errors'])

    errors_by_date = OrderedDict(sorted(errors_by_d.items(), reverse=True))

    print errors_by_date

    print [errors_by_date[x] for x in errors_by_date if errors_by_date[x] != "[[]]"]
    print [len(errors_by_date[x]) for x in errors_by_date]

    # actual_data = [errors_by_date[x] for x in errors_by_date]
    #
    #
    # print 'actual_data', actual_data
    #
    # error_holder = []
    # for i in range(len(actual_data)):
    #     # gets the count of number of errors
    #     error_holder.append([len(x) for x in actual_data[i]].count(1))
    #
    # print 'error_holder', error_holder

    #####################################################################
    # XXX: gathers all tests with timing information by date

    timing_data = {}
    for t in sorted_tests:
        if t["date"] in timing_data:
            timing_data[t["date"]].append({t["test_name"]: t["test_time_diff"]})
        else:
            timing_data[t["date"]] = [{t["test_name"]: t["test_time_diff"]}]

    #####################################################################
    # XXX: retrieves all tags found for tests

    # gets all unique tags
    tag_holder = []
    for test in sorted_tests:
        for t in test["tags"]:
            tag_holder.append(t)

    mytagset = list(set(tag_holder))

    # gets all test names associated with each tag
    full_tag_holder = {}
    for tag in mytagset:
        for test in sorted_tests:
            if tag in test["tags"]:
                if tag in full_tag_holder:
                    full_tag_holder[tag].append(test["test_name"])
                else:
                    full_tag_holder[tag] = [test["test_name"]]

    # gets all *unique* tests names associated with each tag
    for k, v in full_tag_holder.iteritems():
        full_tag_holder[k] = list(set(v))

    #####################################################################

    t_bar_chart = pygal.Bar()
    t_bar_chart.title = "Last 10 Test Runs By Date:"
    t_bar_chart.x_labels = map(str, [x for x in tests_by_date][:10])
    t_bar_chart.add('# of Tests', [len(tests_by_date[x]) for x in tests_by_date][:10])
    t_bar_chart.add('# of Errors', [len(errors_by_date[x]) for x in errors_by_date][:10])
    t_chart = t_bar_chart.render(is_unicode=True)

    return render_template('index.html', tests=sorted_tests, chart=chart, s_chart=s_chart, line_chart=line_c,
                           t_chart=t_chart, timing_data=timing_data, full_tag_holder=full_tag_holder)


@app.route('/analytics/<test_name>')
def individual_analytics(test_name):
    test_info = test_checker(test_name)
    return render_template('individual_test.html', test_info=test_info)


@app.route('/analytics/data')
def data_analytics():

    test_info = data_checker(request.url)

    return render_template('search.html', test_info=test_info)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)


