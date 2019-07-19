import requests

def decimal_check(amount):
	try:
		int(amount.rstrip('0').rstrip('.'))
		return 0
	except:
		return len(str(float(amount)).split('.')[-1])

