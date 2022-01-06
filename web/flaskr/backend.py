import psycopg2
import os
import csv
import json
import time
PG_CONNECTION_STR = "dbname=imdb user=imdb host=localhost"


def get_hint_from_file(idx,file_path="/home/slm/query_log/arms.txt"):
    with open(file_path, "r") as f:
        hints = f.readlines()
    selected = hints[idx].strip()
    hint_set_1 = []
    hint_set_2 = []
    for arm in selected.split(", "):
        if("disable" in arm):
            hint_set_2.append(arm)
            hint_set_1.append(arm.replace("disable","enable")+"=off")
    return hint_set_1, hint_set_2
    


def run_query(sql, with_hint, idx=0):

    try:
        start_time = time.time()
        conn = psycopg2.connect(PG_CONNECTION_STR)
        cur = conn.cursor()
        cur.execute("SET statement_timeout TO 300000")
        if(with_hint==True):
            hints,_ = get_hint_from_file(idx)
            for hint in hints:
                cur.execute("SET {}".format(hint))
        cur.execute(sql)
        sql_result = cur.fetchall()
        conn.close()
        
        with open("/home/slm/query_log/total_cost.txt","a") as f:
            f.write(str(time.time() - start_time)+"\n")
        
        # print(res)
        with open("/home/slm/query_log/query_result.txt","w") as f:
            csv_out = csv.writer(f)
            csv_out.writerows(sql_result)
            
        #save sql query
        with open("/home/slm/query_log/sql.txt","a") as f:
            f.write(sql.replace("\n"," ").strip()+"\n")
        print("Query executed successfully")
        
        # run explain and save plan
        conn = psycopg2.connect(PG_CONNECTION_STR)
        cur = conn.cursor()
        cur.execute("SET statement_timeout TO 300000")
        if(with_hint==True):
            hints, _ = get_hint_from_file(idx)
            for hint in hints:
                cur.execute("SET {}".format(hint))
        cur.execute("explain (FORMAT JSON)" + sql)
        res = cur.fetchall()[0][0][-1]
        conn.close()
        sql_count = len(os.listdir("/home/slm/query_log/plan_log/"))
        with open("/home/slm/query_log/plan_log/{}.json".format(sql_count),"w") as f:
            json.dump(res, f, ensure_ascii=False)
        

        
        if(with_hint==True):
            with open("/home/slm/query_log/arm_cost.txt","r") as f:
                costs = f.readlines()
                costs_f = [float(x) for x in costs]
            min_idx = costs_f.index(min(costs_f))
            _, hints = get_hint_from_file(min_idx)
            with open("/home/slm/query_log/optimization_hints.txt","a") as f:
                f.write(", ".join(hints)+'\n')
        else:
            with open("/home/slm/query_log/optimization_hints.txt","a") as f:
                f.write("No optimization\n")
        
        
        return True, sql_result

    except psycopg2.Error as e:
        print(e.pgerror)
        with open("/home/slm/query_log/query_result.txt","w") as f:
            f.writelines(e.pgerror)
        
        return False, json.dumps(None)
        
        
def optimize_query(sql):

    try:
        sql_count = len(os.listdir("/home/slm/query_log/plan_log/"))
        conn = psycopg2.connect(PG_CONNECTION_STR)
        cur = conn.cursor()
        cur.execute("SET statement_timeout TO 300000")
        cur.execute("explain " + sql)
        conn.close()
        # print(res)
        sql_count_after = len(os.listdir("/home/slm/query_log/plan_log/"))
        for i in range(sql_count,sql_count_after):
            os.remove("/home/slm/query_log/plan_log/{}.csv".format(i))

        print("Query optimized")    
        
        with open("/home/slm/query_log/arms.txt","r") as f:
            arms = f.readlines()
        with open("/home/slm/query_log/arm_cost.txt","r") as f:
            arm_cost = f.readlines()  
        with open("/home/slm/query_log/confidence.txt","r") as f:
            arm_confidence = f.readlines()  
        with open("/home/slm/query_log/optimized_query.sql","w") as f:
            f.write(sql)
    
        return True, arms, arm_cost, arm_confidence

    except psycopg2.Error as e:
        print(e.pgerror)
        with open("/home/slm/query_log/query_result.txt","w") as f:
            f.writelines(e.pgerror)
        
        return False