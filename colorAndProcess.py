import time

from colorama import  init, Fore, Back, Style  
init(autoreset=True)  
class Colored(object):  

    #  前景色:红色  背景色:默认  
    def red(self, s):  
        return Fore.RED + s + Fore.RESET  

    #  前景色:绿色  背景色:默认  
    def green(self, s):  
        return Fore.GREEN + s + Fore.RESET  

    #  前景色:黄色  背景色:默认  
    def yellow(self, s):  
        return Fore.YELLOW + s + Fore.RESET  

    #  前景色:蓝色  背景色:默认  
    def blue(self, s):  
        return Fore.BLUE + s + Fore.RESET  

    #  前景色:洋红色  背景色:默认  
    def magenta(self, s):  
        return Fore.MAGENTA + s + Fore.RESET  

    #  前景色:青色  背景色:默认  
    def cyan(self, s):  
        return Fore.CYAN + s + Fore.RESET  

    #  前景色:白色  背景色:默认  
    def white(self, s):  
        return Fore.WHITE + s + Fore.RESET  

    #  前景色:黑色  背景色:默认  
    def black(self, s):  
        return Fore.BLACK  

    #  前景色:白色  背景色:绿色  
    def white_green(self, s):  
        return Fore.WHITE + Back.GREEN + s + Fore.RESET + Back.RESET  

color = Colored() 

if __name__ == "__main__":
    print()
    for i in range(0,101):
        print(color.yellow( int(i/2)* '.' + ' ' + str(i) + '%'), end='\r')
        time.sleep(0.1)
    print()
