pi = 3.141592653589793238462643383279502884197169399375

class TrigFunctions(object):
	def __init__(self):
		self.__angle = None

	def main(self):
		self.__angle = int(input("Which angle would you like to sin,cos and tan? --> "))
		sigfigs = int(input("How many significant figures --> "))
		print(self.sin(self.__angle,sigfigs))
		print(self.cos(self.__angle,sigfigs))
		print(self.tan(self.__angle,sigfigs))

	def fact(self,value):
		if value == 0 or value == 1:
			return 1
		else:
			return value*self.fact(value-1)

	def __toRadians(self,value):
		return (value/180)*pi

	def __taylorSeries(self,cors,value):
		sign = -1
		if cors == 1:
			valuePH = value
			for i in range(3,14,2):
				valuePH += sign*(value**i)/self.fact(i)
				sign *= -1
		elif cors == 2:
			valuePH = 1
			for j in range(2,15,2):
				valuePH += sign*(value**j)/self.fact(j)
				sign *= -1
		return valuePH

	def sin(self,value,sf):
		value = self.__toRadians(value)
		return round(self.__taylorSeries(1,value),sf)

	def cos(self,value,sf):
		value = self.__toRadians(value)
		return round(self.__taylorSeries(2,value),sf)

	def tan(self,value,sf):
		cosine = self.cos(value, sf)
		if cosine == 0:
			return "Undefined"  
		return round(self.sin(value, sf)/ cosine, sf)


app = TrigFunctions()
app.main()
