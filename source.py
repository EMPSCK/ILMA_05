import re

text = "<p>Картинка <img alt='картинка' src='bg.jpg'> в тексте</p>"
a = re.findall(r"src\s*=\s*('.+?')", text)
print(a)