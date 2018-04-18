#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = '交易策略03'
__author__ = 'JN Zhang'
__mtime__ = '2018/4/6'
"""
import datetime
import numpy as np

from bean.tk_wmacd_bean import tkWMacdBean
from mongo_db.mongodb_manager import DBManager
from t_redis.redis_manager import RedisManager


def cmp_datatime(item):
    return datetime.datetime.strptime(item["cur_timer"], "%Y-%m-%d")


class TsStrategy3:
    def __init__(self):
        self.db_manager_wm = DBManager("wm_details")

    def get_result(self, ticker):
        if isinstance(ticker, tkWMacdBean) and len(ticker.get_wmacd_list()) > 30:
            if ticker.get_wmacd_list()[-1] > 0 >= ticker.get_wmacd_list()[-2]:
                if 0.1 > ticker.get_diff_list()[-1] > 0:
                    if np.mean(ticker.get_tur_list()[-5:-1]) < ticker.get_tur_list()[-1]:
                        return 1
        return -1

    # 将策略结果同步到redis
    def update_redis(self, date):
        db_manager_wm = DBManager("wm_details")
        code_list = db_manager_wm.find_by_id("")
        buy_list = list()
        for item in code_list:
            try:
                code = item["code"]
                price_list = list()
                tur_list = list()
                highest_list = list()
                open_list = list()
                # 获取wmacd数据
                tk_details = self.db_manager_wm.find_by_key({"code": code})[0]
                for tk_item in tk_details["price_list"]:
                    if datetime.datetime.strptime(date, "%Y-%m-%d") >= datetime.datetime.strptime(tk_item["frist_date"], "%Y-%m-%d"):
                        price_list.append(tk_item["close_price"])
                        tur_list.append(tk_item["close_price"])
                        highest_list.append(tk_item["close_price"])
                        open_list.append(tk_item["close_price"])
                wmacd_list, diff_list, dea_list = self.get_w_macd(price_list[:])
                # 创建wmacd实体
                tk_bean = tkWMacdBean(code, price_list, wmacd_list, diff_list, dea_list, tur_list, highest_list, open_list)
                if self.get_result(tk_bean):
                    buy_list.append(code)
            except Exception as e:
                print(str(e))
                continue
        rm = RedisManager()
        rm.set_data("wm_" + str(date), buy_list)

    # 计算当前时间段的wmacd值
    def get_w_macd(self, price_list):
        ema_12_list = list()
        for index in range(len(price_list)):
            if index == 0:
                ema_12_list.append(price_list[0])
            else:
                ema_12_list.append(round(ema_12_list[index - 1] * 11 / 13 + price_list[index] * 2 / 13, 4))
        ema_26_list = list()
        for index in range(len(price_list)):
            if index == 0:
                ema_26_list.append(price_list[0])
            else:
                ema_26_list.append(round(ema_26_list[index - 1] * 25 / 27 + price_list[index] * 2 / 27, 4))
        diff_list = list()
        for index in range(len(ema_12_list)):
            diff = ema_12_list[index] - ema_26_list[index]
            diff_list.append(diff)
        dea_list = list()
        for index in range(len(diff_list)):
            if index == 0:
                dea_list.append(diff_list[0])
            else:
                dea_list.append(round(dea_list[index - 1] * 0.8 + diff_list[index] * 0.2, 4))
        wmacd_list = list()
        for index in range(len(dea_list)):
            bar = (diff_list[index] - dea_list[index]) * 3
            wmacd_list.append(bar)
        return wmacd_list, diff_list, dea_list


if __name__ == "__main__":
    st3 = TsStrategy3()
    st3.update_redis("2018-04-01")
