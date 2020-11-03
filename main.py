#! /usr/bin/env python3

import re
import sys
import json
import getopt
import telegram
import stock.pysnowball.pysnowball as ball
from functools import reduce
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

tgToken = None
ballToken = None
SYMBOL_REGEX_USA = "[￥¥]([a-zA-Z]{1,4})"
SYMBOL_REGEX_A = "[￥¥]((SH[0-9]{6})|(SZ[0-9]{6}))"
SYMBOL_REGEX_HK = "[￥¥]0([0-3][0-9]{3})"
SYMBOL_REGEX_NAME = "[￥¥]((?![a-zA-Z]])\d?[\u4e00-\u9fa5]*[a-zA-Z]*(_\d)?)\s?"


# bot = telegram.Bot(token=tgToken)
# print(bot.get_me())

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=str(update.message))

def stockPrice(update, context):
    ball.set_token(ballToken)
    text = update.message.text
    stockCode = text.replace("/stockPrice", "", 1).strip()
    result = ball.quotec(stockCode)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=result)

def turnover(update, context):
    ball.set_token(ballToken)
    
    resultSH = ball.quotec("SH000001")["data"][0]
    resultSZ = ball.quotec("SZ399001")["data"][0]
    result = "上证指数成交额{}元，成交量{}手；\n" + \
        "深证成指成交额{}元，成交量{}手；\n" + \
        "总成交额{}元，成交量{}手。"
    amountSH = formatBigDecimal(float(resultSH["amount"]))
    amountSZ = formatBigDecimal(float(resultSZ["amount"]))
    volumeSH = formatBigDecimal(float(resultSH["volume"])/100)
    volumeSZ = formatBigDecimal(float(resultSZ["volume"])/100)
    amountTotal = formatBigDecimal(float(resultSH["amount"]) + float(resultSZ["amount"]))
    volumeTotal = formatBigDecimal((float(resultSH["volume"]) + float(resultSZ["volume"]))/100)
    result = result.format(amountSH, volumeSH, amountSZ, volumeSZ, amountTotal, volumeTotal)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=result)

def searchForNameAndCode(query, index = 1):
    jsonObj = ball.searchCode(query, index)
    if len(jsonObj["stocks"]) > 0:
        stockNameList = list(map(lambda x:x["name"], jsonObj["stocks"]))
        stock = jsonObj["stocks"][-1]
        return stock["code"], stock["name"], stockNameList
    return None, None, None

def formatBigDecimal(num):
    if num >= 100000000:
        return str("%.1f"%(num / 100000000)) + "亿"
    elif num >= 10000:
        return str("%d"%(num / 10000)) + "万"
    else:
        return str(num)

def distinctSymbol(slist, x):
    repeat = None
    if type(slist) is not list:
        slist = [slist]
    for s in slist:
        if (x in s) or (s in x):
            repeat = s
            break
    if repeat == None:
        slist.append(x)
    elif(len(x) > len(repeat)):
        slist.remove(repeat)
        slist.append(x)
    return slist

def handleSymbol(update, context):

    text = ""
    if update.message != None:
        text = update.message.text
    
    symbols = []
    symbols += list(map(lambda x:x[0], re.findall(SYMBOL_REGEX_A, text)))
    symbols += list(map(lambda x:x[0], re.findall(SYMBOL_REGEX_NAME, text)))
    symbols += list(re.findall(SYMBOL_REGEX_USA, text))
    if len(symbols) > 0:
        if len(symbols) > 1:
            symbols = reduce(distinctSymbol, symbols)
        print("handleSymbol " + str(symbols))
        context.bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
        ball.set_token(ballToken)
        for symbol in symbols:
            # update.message.reply_text(
            #             text=ball.searchCode(symbol), parse_mode=telegram.ParseMode.MARKDOWN
            #         )
            index = 1
            if "_" in symbol:
                symbolAndIndex = symbol.split("_")
                symbol = symbolAndIndex[0]
                index = int(symbolAndIndex[1])
            code, name, stockNameList = searchForNameAndCode(symbol, index)
            if code != None:
                resultJson = ball.quotec(code)
                if "data" in resultJson:
                    stockNames = ""
                    if len(stockNameList) > 1:
                        for stockName in stockNameList:
                            print(" ==== " + stockName)
                            stockNames += str(stockName) + " "
                    if len(stockNames) > 1:
                        stockNames = stockNames + "\n" + "-------------" + "\n"
                    resultJson = resultJson["data"][0]
                    print(resultJson)
                    price = "当前股价 " + (str(resultJson["current"]) if resultJson["current"] else "无" )
                    percent = ", 涨跌 " + (str(resultJson["percent"]) + "% " + str(resultJson["chg"]) \
                        if (resultJson["percent"] and resultJson["chg"]) else "无" )
                    amount = formatBigDecimal(float(resultJson["amount"])) + "元" if resultJson["amount"] else None
                    volume = formatBigDecimal(float(resultJson["volume"])/100) + "手 " if resultJson["volume"] else None
                    turnover_rate = ", 换手率 " + str(resultJson["turnover_rate"]) + "%" if resultJson["turnover_rate"] else ""
                    amount = ", 成交量 " + volume + amount if (volume and amount) else ""
                    resultText = stockNames + name + " " + str(code) + " " + price + percent + amount + turnover_rate
                    update.message.reply_text(
                        text=resultText, parse_mode=telegram.ParseMode.MARKDOWN
                    )

def main(argv):
    global tgToken
    global ballToken

    opts, args = getopt.getopt(argv, "t:b:")
    for opt, arg in opts:
        if opt == "-t":
            tgToken = arg
        elif opt == "-b":
            ballToken = arg
    if (tgToken == None) or (ballToken == None):
        print("tgToken(-t) and snowballToken(-b) must not be NONE")
        return

    updater = Updater(token=tgToken)
    dispatcher = updater.dispatcher

    symbol_handler = MessageHandler(Filters.text & (~Filters.command), handleSymbol)
    dispatcher.add_handler(symbol_handler)

    # start_handler = CommandHandler('start', start)
    # dispatcher.add_handler(start_handler)
    # stock_handler = CommandHandler('stockPrice', stockPrice)
    # dispatcher.add_handler(stock_handler)
    stock_handler = CommandHandler('turnover', turnover)
    dispatcher.add_handler(stock_handler)

    updater.start_polling()

if __name__ == '__main__':
    main(sys.argv[1:])
