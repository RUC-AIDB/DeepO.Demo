import os

from flask import Flask, request, render_template
from flask import send_from_directory
from flask.templating import render_template_string
from .backend import run_query, optimize_query
import json

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/<path:filename>')
    def serve_static(filename):
        return render_template(filename)
    
    @app.route('/',methods=['GET','POST'])
    def home():
        if request.method=='GET':
            return render_template("sql_tool.html")
        else:
            query = request.form["query"]
            print(query)
            return render_template("sql_tool.html")

    @app.after_request
    def after_request(resp):
        resp.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,session_id')
        resp.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS,HEAD')
        # 这里不能使用add方法，否则会出现 The 'Access-Control-Allow-Origin' header contains multiple values 的问题
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    
    @app.route('/favicon.ico') 
    def favicon(): 
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.route('/pg_run', methods=['POST'])
    def run_with_pg():
        sql = request.values['sql']
        print ("run with postgresql")
        status, result_json = run_query(sql, with_hint=False)
        if(status==True):
            return {
                "data": result_json
            }
        else:
            return {}

    @app.route('/deepo_optimize', methods=['POST'])
    def optimize_with_deepo():
        sql = request.values['sql']
        print ("optimized with deepo")
        status, arms, arm_cost, arm_confidence = optimize_query(sql)
        # print(arms)
        if(status==True):
            return{
            "info_arm": arms,
            "info_cost": arm_cost,
            "info_confidence": arm_confidence
        }
        else:
            return {}, {}
    
    @app.route('/submit', methods=['POST'])
    def submit():
        with_hint = True
        selected_arm = int(request.values['selection'])-1
        print("selected arm: ", selected_arm)
        with open("/home/slm/query_log/optimized_query.sql","r") as f:
            sql = f.read()
        status, result = run_query(sql,with_hint=with_hint,idx=selected_arm)
        print("with hint: ", with_hint)
        if(status==True):
            return {
                "data": result
            }
        else:
            return {}
        
    @app.route('/compare',methods=['POST'])
    def compare():
        selected_history = request.values['data']
        selected_history = [x for x in selected_history.split(",")[:2]]
        with open("/home/slm/query_log/comparison_selection.txt","w") as f:
            f.writelines("\n".join(selected_history))
        
        # # TODO: assert there are only two selected history
        print(selected_history)
        # with open("/home/slm/query_log/total_cost.txt","r") as f:
        #     info_cost = f.readlines()
        # with open("/home/slm/query_log/sql.txt","r") as f:
        #     info_sql = f.readlines()
        # with open("/home/slm/query_log/optimization_hints.txt","r") as f:
        #     info_hints = f.readlines()
        # cost_1, cost_2 = info_cost[selected_history[0]],info_cost[selected_history[1]]
        # sql_1, sql_2 = info_sql[selected_history[0]],info_sql[selected_history[1]]
        # assert sql_1==sql_2, "not same query"
        # hint_1, hint_2 = info_hints[selected_history[0]],info_hints[selected_history[1]]
        # with open("/home/slm/query_log/plan_log/{}.json".format(selected_history[0]),"r") as f:
        #     plan_1 = json.load(f)
        # with open("/home/slm/query_log/plan_log/{}.json".format(selected_history[1]),"r") as f:
        #     plan_2 = json.load(f)
        # res = {
        #     "cost_1":cost_1,
        #     "cost_2":cost_2,
        #     "sql":sql_1,
        #     "hint_1":hint_1,
        #     "hint_2":hint_2,
        #     "plan_1":plan_1,
        #     "plan_2":plan_2
        # }
        # return render_template("optimization_analysis.html",data=res)
        return {}
    
    @app.route('/default', methods=['POST'])
    def default():
        print("selected arm: default")
        with open("/home/slm/query_log/optimized_query.sql","r") as f:
            sql = f.read()
        status, result = run_query(sql,with_hint=False)
        # print(result)
        if(status==True):
            return {
                "data": result
            }
        else:
            return {}        

    @app.route('/queryHistory',methods=['POST'])
    def queryHistory():
        with open("/home/slm/query_log/total_cost.txt","r") as f:
            info_cost = f.readlines()
        with open("/home/slm/query_log/sql.txt","r") as f:
            info_sql = f.readlines()
        with open("/home/slm/query_log/optimization_hints.txt","r") as f:
            info_hints = f.readlines()
        return{
            "info_sql": info_sql,
            "info_cost": info_cost,
            "info_hints": info_hints
        }
    
    @app.route('/optimization_analysis',methods=['POST'])
    def optimization_analysis():
        with open("/home/slm/query_log/comparison_selection.txt","r") as f:
            selection = f.readlines()
        selected_history = [int(x) for x in selection]
        # # TODO: assert there are only two selected history
        print(selected_history)
        with open("/home/slm/query_log/total_cost.txt","r") as f:
            info_cost = f.readlines()
        with open("/home/slm/query_log/sql.txt","r") as f:
            info_sql = f.readlines()
        with open("/home/slm/query_log/optimization_hints.txt","r") as f:
            info_hints = f.readlines()
        cost_1, cost_2 = info_cost[selected_history[0]],info_cost[selected_history[1]]
        sql_1, sql_2 = info_sql[selected_history[0]],info_sql[selected_history[1]]
        assert sql_1==sql_2, "not same query"
        hint_1, hint_2 = info_hints[selected_history[0]],info_hints[selected_history[1]]
        with open("/home/slm/query_log/plan_log/{}.json".format(selected_history[0]),"r") as f:
            plan_1 = f.read()
        with open("/home/slm/query_log/plan_log/{}.json".format(selected_history[1]),"r") as f:
            plan_2 = f.read()
        res = {
            "cost_1":cost_1,
            "cost_2":cost_2,
            "sql":sql_1,
            "hint_1":hint_1,
            "hint_2":hint_2,
            "plan_1":plan_1,
            "plan_2":plan_2
        }
        return res
        
    return app