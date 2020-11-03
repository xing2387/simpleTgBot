# simpleTgBot
简单的tg bot，自用，no pr no comment

### 目前功能
#### 股票Bot
- 使用了[@uname-yang的雪.球的接口](https://github.com/uname-yang/pysnowball)
- 输入 "￥内容" 即可会返回一条和"内容"相关的股票的一些实时(?)信息
- 输入 "￥内容_5" 即可会返回至多5个相关的股票名称，和其中最后的那个的股票的一些实时(?)信息
- /turnover命令返回上证和深指当日目前的成交额

## 运行
```shell
    ./main.py -t tgBot的token -b 雪.球api的token
```
## 相关
- 雪.球api来源和token获取： https://github.com/uname-yang/pysnowball
