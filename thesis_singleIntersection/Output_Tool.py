

import os
import sys
import optparse
import collections

# 引入 configparser 模組
import configparser




if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
    import sumolib  # noqa
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

def main():
    print("")
    # 建立 ConfigParser
    config = configparser.ConfigParser()
    # 讀取 INI 設定檔
    config.read('experiment_settings.ini')
    # 取得設定值
    #print(config['BackgroundPlan']['green[0]'])
    # 列出所有區段
    #print(config.sections())
    # 列出 BackgroundPlan 區段下所有設定
    for k in config['BackgroundPlan']:
        print("{}: {}".format(k, config['BackgroundPlan'][k]))



if __name__ == "__main__": #當程式直接被執行時會讀這行
    main()
