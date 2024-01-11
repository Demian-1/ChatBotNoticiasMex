# %%
import tkinter as tk
from bs4 import BeautifulSoup
import requests

import torch
from transformers import BertTokenizerFast, EncoderDecoderModel
from transformers import T5ForConditionalGeneration, AutoTokenizer
from transformers import pipeline
nlp = pipeline("question-answering", model="PlanTL-GOB-ES/roberta-large-bne-sqac")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

ckpt_sum = 'mrm8488/bert2bert_shared-spanish-finetuned-summarization'
tokenizer_sum = BertTokenizerFast.from_pretrained(ckpt_sum)
model_sum = EncoderDecoderModel.from_pretrained(ckpt_sum).to(device)

def generate_summary(text):
  inputs = tokenizer_sum([text], padding="max_length", truncation=True, max_length=512, return_tensors="pt")
  input_ids = inputs.input_ids.to(device)
  attention_mask = inputs.attention_mask.to(device)
  output = model_sum.generate(input_ids, attention_mask=attention_mask)
  return tokenizer_sum.decode(output[0], skip_special_tokens=True)

# %%
news = {}
messages = {}
sumaries = {}
current_conversation = [""]
message_entry = None
messsages_text = None

# %%
def get_answer(question, context):
  resp = nlp(question, context)['answer']

  return resp


def add_conversation(conversation): # ,conversation_menu
    if conversation not in messages:
        messages[conversation] = []

    # conversation_menu["values"] = tuple(messages.keys())

def change_conversation(conversation=None):
    if conversation:
        current_conversation[0] = conversation
    load_messages()

def load_messages():
    # current_conversation = self.conversation_menu.get()

    messages_text.config(state="normal")
    messages_text.delete(1.0, tk.END)

    for sender, message in messages.get(current_conversation[0], []):
        messages_text.insert(tk.END, f"{sender}: {message}\n\n")

    messages_text.config(state="disabled")

def send_message(sender=None, message=None):
    # current_conversation = self.conversation_menu.get()
    if not sender:
        sender = "Usuario"
    if not message:
        if message_entry:
            message = message_entry.get()
        else:
            message = "Error no message entry"

    if message:
        messages[current_conversation[0]].append((sender, message))
        if message_entry:
            message_entry.delete(0, "end")
        load_messages()
        
def send_message_and_resp():
    message = message_entry.get()
    send_message()
    send_message("ChatBot",get_answer(context=news[current_conversation[0]], question=message))
 
class ScrolledCanvas():
    def __init__(self, parent, color='white'):
        canv = tk.Canvas(parent, bg=color, relief=tk.SUNKEN)
        canv.config(width=420, height=200)                
 
        ##---------- scrollregion has to be larger than canvas size
        ##           otherwise it just stays in the visible canvas
        canv.config(scrollregion=(0,0,300, 80*len(news)))         
        canv.config(highlightthickness=0)                 

        ctr=0
        for new in news:
            result = get_Titulo(new)
            frm = tk.Frame(parent, width=100, height=90, bg="#cfcfcf",bd=1)
            frm.config(relief=tk.SUNKEN)
            tk.Label(frm, text="Noticia #"+str(ctr+1)+":", font='Helvetica 9').grid(row=0, column=0, sticky="w")
            tk.Button(frm, text=result, command=lambda c=result: change_conversation(c), font='Helvetica 12 bold').grid(row=1, column=0)
            canv.create_window(10,10+(80*ctr),anchor=tk.NW, window=frm)
            ctr+=1
 
        ybar = tk.Scrollbar(parent)
        ybar.config(command=canv.yview)                   
        ## connect the two widgets together
        canv.config(yscrollcommand=ybar.set)              
        ybar.pack(side=tk.RIGHT, fill=tk.Y)                     
        canv.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)
        
def get_Titulo(new):
    input_string = new
    result = input_string.split("_", 1)[0].strip()
    return result

def get_Noticia(new):
    input_string = new
    result = input_string.split("_", 1)[1]
    return result

def get_Noticias():
    url = "https://www.jornada.com.mx/rss/edicion.xml?v=1"

    page_to_scrape = requests.get(url)
    soup = BeautifulSoup(page_to_scrape.text.encode('latin-1').decode('utf-8'), "xml")

    newsItems = soup.findAll("item")

    print(newsItems[0])
    print(newsItems[1])
    
    res = {}

    for new in newsItems:
        # omitir opinion
        link = new.find("link").text
        if "opinion" in link:
            continue

        # construir noticia
        title = new.find("title")
        desc = new.find("description")
        txt = title.text + " _ " + desc.text
        res[get_Titulo(txt)]=txt
        
    return res

def set_conversations():
    for new in news:
        titulo = get_Titulo(news[new])
        print(titulo)
        add_conversation(titulo)
        current_conversation[0] = titulo
        change_conversation()
        send_message("ChatBot",titulo)
        send_message("ChatBot","Resumen: "+sumaries[titulo])
        send_message("ChatBot","Completa: "+get_Noticia(news[new]))
    
    first_key = list(news.keys())[0]
    current_conversation[0] = get_Titulo(news[first_key])
    change_conversation()
    
def set_sumaries():
    for new in news:
        sumaries[new] = generate_summary(new)

# %%
for new in news:
    print(new)

# %%
set_sumaries()

# %%
# sumaries

# %%
window = tk.Tk()
window.title("Simple Text Editor")

window.rowconfigure(0, minsize=300, weight=1)
window.columnconfigure(1, minsize=300, weight=1)

frm_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)
frm_buttons.grid(row=0, column=0, sticky="ns")

chat_frame = tk.Frame(window, bd=2)
chat_frame.grid(row=0, column=1, sticky="nsew")

# Inicializar el área de conversación
messages_text = tk.Text(chat_frame, wrap="word", state="disabled", font="Helvetica 12")
messages_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
scrollbar = tk.Scrollbar(chat_frame, command=messages_text.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
messages_text["yscrollcommand"] = scrollbar.set

# Inicializar el campo de entrada de mensajes
message_entry = tk.Entry(chat_frame, width=50, font="Helvetica 12")
message_entry.grid(row=1, column=0, padx=5, pady=5, sticky="w")
tk.Button(chat_frame, text="Enviar Mensaje", command=send_message_and_resp).grid(row=1, column=1, pady=5)

news = get_Noticias()
messages = {}
set_conversations()

print(messages)

ScrolledCanvas(frm_buttons)
window.mainloop()


