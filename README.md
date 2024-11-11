# Doorbell_Project
Create an App that alerts when a phone signal is detected and plays a message with the name if known. Mainly for hearing impaired, people living remotely and distracted gamers.

(Testers needed. I live in remote location. Tried first version in town and found a lot of signals so know it works. Maybe I'll address that later as it's meant for people without dogs to notify them of someone (or a stranger if i can add a known signals part) approaching their house.)

1. App needs to prompt for names of discovered wifi signal or signals at first use then check db at next startup for those signals and ignoring them as seperate home signals

2. Signals after the first minute of startup, not including home, will be checked against database and announced as "Visitor approaching. <name> is <random welcome>" if known or "Visitor Approaching. Unknown signal detected. Warning. Warning" then prompted to name and add to database

3. The program should remain quiet if signals have been announced but keep scanning in the background and only announce new signals not in database or known signals not seen for one hour



Packages/Requirments: 
pip install pywifi pyttsx3 pillow pystray comtypes 
