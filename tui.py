from textual.app import App
from textual.containers import Container
from textual.widgets import Footer, Header, Button, Static, TextArea, Tabs, TabbedContent, TabPane, LoadingIndicator, Markdown, Select
from psi import Evaluator
from threading import Thread
import sys

def fetchModelList():
    import requests
    import json

    rawData = requests.get('https://openrouter.ai/api/v1/models').text
    parsedData= json.loads(rawData)

    result=[]
    for model in parsedData["data"]:
        result.append({
            "name":model["name"],
            "id":model["id"],
            "modality":model["architecture"]["modality"],
            "prompt_price":model["pricing"]["prompt"],
            "completion_price":model["pricing"]["completion"]
        })

    result=sorted(result,key=lambda x:x["name"])

    return(result)

modelList=fetchModelList()
modelNameList=[(model["name"],model["id"]) for model in modelList]

class Psi(App):

    CSS_PATH="style.css"

    def compose(self):
        global modelNameList
        yield Header()
        yield Footer()

        yield Tabs()

        with TabbedContent():
            #Aba da entrada
            with TabPane("Entrada",id="entrada"):
                yield Select(
                    modelNameList,
                    prompt="Por favor escolha um modelo",
                    id="model_selection",
                    allow_blank=False
                )

                with Container(id="caixa_entrada_valores"):
                    yield Static("Valores empresariais",id="titulo_caixa_valores")
                    yield TextArea(id="entrada_valores",read_only=False)
                
                
                with Container(id="caixa_entrada_prompt"):
                    yield Static("Prompt",id="titulo_caixa_prompt")
                    yield TextArea(id="entrada_prompt",read_only=False)
                yield Button("Enviar", id="enviar")
            
            #Aba da saída
            with TabPane("Saída",id="saida"):
                yield Markdown(id="texto_saida")
                yield LoadingIndicator(id="carregando",classes="hidden")

                yield Markdown("**Ética**",id="etica",classes="eval_result")
                yield Markdown("**Moral**",id="moral",classes="eval_result")
                yield Markdown("**Efetividade econômica**",id="efetividade_economica",classes="eval_result")
                yield Markdown("**Valores empresariais**",id="valores_empresariais",classes="eval_result")
    
    async def on_button_pressed(self, event):
        if event.button.id=="enviar":
            if not "sent" in self.query_one("#enviar").classes: #Querries to check if button has already been pressed
                #Fix this
                #thread=Thread(target=self.action_enviar, args=(self,))
                #thread.start()
                #self.action_enviar()
                self.setup_enviar()
                self.run_worker(self.action_enviar(),thread=True)
# UNCOMENT PREVIOUS LINE
    def setup_enviar(self):
        self.query_one("#enviar").add_class("sent")
        self.query_one("#enviar").can_focus=False
        self.query_one("#entrada_valores").read_only=True
        self.query_one("#entrada_prompt").read_only=True
        self.query_one(TabbedContent).disable_tab("entrada")
        self.query_one("#carregando").remove_class("hidden")

    async def action_enviar(self):
    #def action_enviar(self):
        values=str(self.query_one("#entrada_valores").text)
        prompt=str(self.query_one("#entrada_prompt").text)

        if values=="" or prompt=="":
            sys.exit("Enter a prompt and the corporate values")
        
        e=Evaluator(model_id=self.query_one("#model_selection").value)
        
        ans=e.find_action(prompt,values)
        self.query_one("#texto_saida").update(ans.action_plan)

        eval_results_md={
            "<adequado>":'`✓ Adequado`',
            "<inconclusivo>":'`— Inconclusivo`',
            "<inadequado>":'**`🗙 Inadequado`**'
        }

        self.query_one("#etica").update("**Ética**: "+eval_results_md[ans.evaluation["etica"]])
        self.query_one("#moral").update("**Moral**: "+eval_results_md[ans.evaluation["moral"]])
        self.query_one("#efetividade_economica").update("**Efetividade econômica**: "+eval_results_md[ans.evaluation["efetividade_economica"]])
        self.query_one("#valores_empresariais").update("**Valores empresariais**: "+eval_results_md[ans.evaluation["valores_empresariais"]])
        self.query_one("#carregando").add_class("hidden")
        
if __name__=="__main__":
    app=Psi()
    app.run()