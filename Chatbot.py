def chatbot():
    print("🤖 ChatBot: Hello! I am your assistant. Type 'quit' to exit.\n")
    
    responses = {
        "hello": "Hi there! How can I help you?",
        "how are you": "I am doing great, thanks for asking!",
        "name": "I am PyBot, your Python assistant!",
        "help": "I can answer basic questions. Try asking my name!",
        "bye": "Goodbye! Have a great day!",
        "karachi": "Karachi is the largest city in Pakistan! 🏙️",
        "python": "Python is an amazing programming language! 🐍"
    }

    while True:
        user_input = input("You: ").lower()
        
        if user_input == "quit":
            print("🤖 ChatBot: Bye bye!")
            break
        
        matched = False
        for key in responses:
            if key in user_input:
                print(f"🤖 ChatBot: {responses[key]}")
                matched = True
                break
        
        if not matched:
            print("🤖 ChatBot: I don't understand that yet. Try asking something else!")

chatbot()
