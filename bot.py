import ccxt, config
import pandas as pd
from ta.trend import EMAIndicator
import winsound
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL
from binance.exceptions import BinanceAPIException
import time

api_key = 'xxx'
api_secret = 'xxx'

client = Client(api_key, api_secret)

duration = 1000 #milliseconds
freq = 440 #fr

symbolName = input('Cripto a operar vs BUSD')
symbol = str(symbolName) + "/BUSD"
slowEMAValue = input('slow firt-value value')
fastEMAValue = input('fast firt-value value')
kesisim = False
longPozisyonda = False
shortPozisyonda = False
lastPriceActive = 0
stopLossThreshold = 100 
marketStopLossThreshold = 200
numberOfLaps = 0
activateExit = False

exitingPosition = False

exchange = ccxt.binance({
    "apiKey": api_key,
    "secret": api_secret,

    "options":{
        "defaultType": "future"
    },
    'enableRateLimit': True
})



first_value = 5
double_value = 10

quantity_input = first_value

def buy(price, limit_or_market, quantity):
    order = client.futures_create_order(
        symbol='BTCBUSD',
        side=SIDE_BUY,
        type=Client.ORDER_TYPE_LIMIT if limit_or_market else Client.ORDER_TYPE_MARKET,
        quantity=quantity,
        price=price,
        timeInForce='GTX'
    )

    print(order)

def sell(price, limit_or_market, quantity):
    order = client.futures_create_order(
        symbol='BTCBUSD',
        side=SIDE_SELL,
        type=Client.ORDER_TYPE_LIMIT if limit_or_market else Client.ORDER_TYPE_MARKET,
        quantity=quantity,
        price=price,
        timeInForce='GTX'
    )
    print(order)



while True:
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe='5m', since= None, limit=1500)
        df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])

        # LOAD EMA CLOSING
        slowEMA = EMAIndicator(df['close'], float(slowEMAValue))
        df['Slow EMA'] = slowEMA.ema_indicator()

        # LOAD FAST EMA
        fastEMA = EMAIndicator(df['close'], float(fastEMAValue))
        df['Fast EMA'] = fastEMA.ema_indicator()
        
        
        open_orders = exchange.fetch_open_orders(symbol)
        if len(open_orders) > 0:
            print("Hay Ordenes")
            print('price at which buy : ', open_orders[0]['info']['price'])
            print(f"lastPriceActive :{lastPriceActive}, price: {float(df['close'].iloc[-1])}")
            print(f"longPozisyonda :{longPozisyonda}, shortPozisyonda: {shortPozisyonda}")
            print(f"Long gap: {float(df['close'].iloc[-1]) - float(open_orders[0]['info']['price'])}")
            print(f"Short gap: {float(open_orders[0]['info']['price']) - float(df['close'].iloc[-1])}")
            print(f"--------------------------------------------------------------------")

            if(longPozisyonda):
                if((float(df['close'].iloc[-1]) - float(open_orders[0]['info']['price'])) >= 20):
                    print("Existen órdenes abiertas. Cerrando las órdenes...")

                    for order in open_orders:
                        exchange.cancel_order(order['id'], symbol)
                    numberOfLaps = 0
                    activateExit = True
                    time.sleep(2)  # Esperar 2 segundos después de cancelar las órdenes
                    continue

            elif(shortPozisyonda):
                if(float(open_orders[0]['info']['price']) - (float(df['close'].iloc[-1])) >= 20):
                    print("Existen órdenes abiertas. Cerrando las órdenes...")

                    for order in open_orders:
                        exchange.cancel_order(order['id'], symbol)
                    numberOfLaps = 0
                    activateExit = True
                    time.sleep(2)  # Esperar 2 segundos después de cancelar las órdenes
                    continue
            continue

        positions = exchange.fetch_positions([symbol])
        entryPrice = float(positions[0]['entryPrice'])
        close = float(df['close'].iloc[-1] - 1)

        print('posiciones:')
        print(positions)
        print(f'entryPrice: {entryPrice}')
        print(f'close: {close}')
        print(f'lastPriceActive: {lastPriceActive}')
        print(f'activateExit: {activateExit}')
        print('----------------------------------------------------------------------------------')

        # STOP LOSS
        if(positions):
            if float(positions[0]['contracts']) != 0:
                if close >= entryPrice + 100 or close <= entryPrice - 100:
                    print('Salir de la posicion')
                    print(f'entryPrice: {entryPrice}, close: {close}')

                    if(positions[0]['side'] == 'long'):
                        try:
                            if longPozisyonda:
                                print('LONG EXIT')
                                longPozisyonda = False

                            sell(price=float(df['close'].iloc[-1] + 1), limit_or_market = True, quantity=float(positions[0]['contracts']))
                            shortPozisyonda = True
                            print(float(df['close'].iloc[-1] + 1))
                            numberOfLaps = 0
                            lastPriceActive = float(df['close'].iloc[-1] + 1)

                            winsound.Beep(freq, duration)
                        except BinanceAPIException as error:
                            print(f"Error sell: {error}")
                            print(f"sell: {df['close'].iloc[-1] + 1}")
                            continue

                    elif (positions[0]['side'] == 'short'):
                        try:
                            if longPozisyonda:
                                print('LONG EXIT')
                                longPozisyonda = False
                        
                            buy(price=float(df['close'].iloc[-1] - 1), limit_or_market = True, quantity=float(positions[0]['contracts']))
                            longPozisyonda = True
                            print(float(df['close'].iloc[-1] - 1))
                            numberOfLaps = 0
                            lastPriceActive = (df['close'].iloc[-1] - 1)

                            winsound.Beep(freq, duration)
                        except BinanceAPIException as error:
                            print(f"Error buy: {error}")
                            print(f"buy: {df['close'].iloc[-1] - 1}")
                            continue
                

        if positions and activateExit:
            print('tenemos algo que sacar')
            if float(positions[0]['info']['positionAmt']) != 0:
                print("Vamos a cerrar esa orden")
                if(positions[0]['side'] == 'long'):
                    print("Tenemos que cerrar un Long")
                    try:
                        if longPozisyonda:
                            print('LONG EXIT')
                            longPozisyonda = False

                        sell(price=float(df['close'].iloc[-1] + 1), limit_or_market = True, quantity=float(positions[0]['contracts']))
                        print(float(df['close'].iloc[-1] + 1))
                        shortPozisyonda = True
                        numberOfLaps = 0
                        activateExit = False
                        lastPriceActive = float(df['close'].iloc[-1] + 1)
                        winsound.Beep(freq, duration)
                    except BinanceAPIException as error:
                        print(f"Error sell: {error}")
                        print(f"sell: {df['close'].iloc[-1] + 1}")
                        continue

                elif (positions[0]['side'] == 'short'):
                    print("Tenemos que cerrar un short")
                    try:
                        if shortPozisyonda:
                            print('SHORT EXIT')
                            shortPozisyonda = False

                        buy(price=float(df['close'].iloc[-1] - 1), limit_or_market = True, quantity=float(positions[0]['contracts']))
                        print(float(df['close'].iloc[-1] - 1))
                        longPozisyonda = True
                        numberOfLaps = 0
                        activateExit = False
                        lastPriceActive = (df['close'].iloc[-1] - 1)
                        winsound.Beep(freq, duration)
                    except BinanceAPIException as error:
                        print(f"Error buy: {error}")
                        print(f"buy: {df['close'].iloc[-1] - 1}")
                        continue

                time.sleep(1)  # Esperar 1 segundos antes de realizar la próxima iteración del bucle
                continue

            else:
                activateExit = False
                time.sleep(1)  
                continue



        if (df["Fast EMA"][len(df.index) - 3] < df['Slow EMA'][len(df.index) - 3] and
                df["Fast EMA"][len(df.index) - 2] > df['Slow EMA'][len(df.index) - 2]) or \
                (df["Fast EMA"][len(df.index) - 3] > df['Slow EMA'][len(df.index) - 3] and
                 df["Fast EMA"][len(df.index) - 2] < df['Slow EMA'][len(df.index) - 2]):
            kesisim = True

        bars1m = exchange.fetch_ohlcv(symbol, timeframe='1m', since= None, limit=1500)
        df1m = pd.DataFrame(bars1m, columns=["timestamp", "open", "high", "low", "close", "volume"])

        # LONG ENTER
        if kesisim and df["Fast EMA"][len(df.index) - 2] > df['Slow EMA'][len(df.index) - 2] and longPozisyonda == False:
            if float(df1m["close"].iloc[-1]) > float(df1m["open"].iloc[-1]) + 5:
                    print('ya no voy a entrar')
                    continue;

            if shortPozisyonda:
                print('SHORT EXIT')
                shortPozisyonda = False
            
            if positions and float(positions[0]['contracts']) != 0 and positions[0]['side'] == 'long':
                print('lo saco por que hay una pocision de la misma')
                longPozisyonda = False
                continue

            if positions and float(positions[0]['contracts']) != 0 and positions[0]['side'] == 'short':

                if abs(float(positions[0]['info']['positionAmt'])) < first_value :
                    quantity_input = abs(float(positions[0]['info']['positionAmt'])) + first_value

                elif abs(float(positions[0]['info']['positionAmt'])) == first_value :
                    quantity_input = double_value

                elif abs(float(positions[0]['info']['positionAmt'])) > first_value :
                    quantity_input = abs(float(positions[0]['info']['positionAmt']))

            else:
                quantity_input = first_value


            try:
                print('LONG ENTER')
                buy(price=float(df1m["close"].iloc[-1] - 1), limit_or_market = True, quantity=5)
                print('price: ', df1m["open"].iloc[-1] - 1)
                longPozisyonda = True
                lastPriceActive = float(df1m["open"].iloc[-1] - 1)
                winsound.Beep(freq, duration)
            except BinanceAPIException as error:
                print(f"Error buy: {error}")
                print(f"buy: {df1m['open'].iloc[-1] - 1}")
                continue

            

        # SHORT ENTER
        if kesisim and df["Fast EMA"][len(df.index) - 2] < df['Slow EMA'][len(df.index) - 2]  and shortPozisyonda == False:
            if float(df["open"].iloc[-1]) - 5 > float(df1m["close"].iloc[-1]):
                print('ya no voy a entrar')
                continue;
            
            if longPozisyonda:
                print('LONG EXIT')
                longPozisyonda = False

            if positions and float(positions[0]['contracts']) != 0 and (positions[0]['side'] == 'short'):
                print('lo saco por que hay una pocision de la misma')
                shortPozisyonda = False
                continue

            if positions and float(positions[0]['contracts']) != 0 and positions[0]['side'] == 'long':

                if float(positions[0]['info']['positionAmt']) < first_value :
                    quantity_input = float(positions[0]['info']['positionAmt']) + first_value
                
                elif float(positions[0]['info']['positionAmt']) == first_value :
                    quantity_input = double_value

                elif float(positions[0]['info']['positionAmt']) > first_value :
                    quantity_input = float(positions[0]['info']['positionAmt'])
            
            else:
                quantity_input = first_value

            try:
                print("SHORT ENTER")
                sell(price=float(df1m["close"].iloc[-1] + 1), limit_or_market = True, quantity=quantity_input)
                print(float(df1m["open"].iloc[-1] + 1))
                shortPozisyonda = True
                lastPriceActive = float(df1m["open"].iloc[-1] + 1)
                winsound.Beep(freq, duration)
            except BinanceAPIException as error:
                print(f"Error sell: {error}")
                print(f"sell: {df1m['open'].iloc[-1] + 1}")
                continue
        


        print(df)

    except Exception as e:
        print(f"Error during execution: {e}")
        print("Retrying in 5 seconds...")
        time.sleep(5)  # Espera 5 segundos antes de reintentar
        continue
