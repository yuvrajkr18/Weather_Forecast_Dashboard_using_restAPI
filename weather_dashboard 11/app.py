"""Weather Forecast Dashboard - Tkinter + OpenWeatherMap REST API.
Core dashboard follows the supplied micro-project report. The Planner tab is an
additional weather-aware activity scheduler requested for this version.
"""
import json, queue, threading
from pathlib import Path
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from exceptions import WeatherError
from services.api_client import WeatherAPIClient
from services.analyzer import WeatherAnalyzer
from services.chart import ChartPlotter
from services.storage import StorageManager

ROOT=Path(__file__).resolve().parent
CONFIG=json.loads((ROOT/"config.json").read_text())
BG="#0b1220"; PANEL="#131f33"; PANEL2="#1a2940"; ACCENT="#66b8ff"; TEXT="#edf4ff"; MUTED="#9aabc2"

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Weatherly | Forecast Dashboard"); self.geometry("1180x850"); self.minsize(1000,740); self.configure(bg=BG)
        self.client=WeatherAPIClient(CONFIG.get("api_key","")); self.store=StorageManager(ROOT/"data"); self.results=queue.Queue(); self.current=None; self.forecast=[]; self.weather_icon=None; self.icon_photo=None; self.unit=tk.StringVar(value=CONFIG.get("unit","C")); self.city_var=tk.StringVar(value=CONFIG.get("default_city","Bengaluru"))
        self._style(); self._build(); self.after(200,self._poll_results); self.after(1000,self._clock); self.after(5000,self._auto_refresh); self.search()

    def _style(self):
        s=ttk.Style(self); s.theme_use("clam"); s.configure("TNotebook",background=BG,borderwidth=0); s.configure("TNotebook.Tab",background=PANEL2,foreground=TEXT,padding=(18,10),font=("Helvetica",10,"bold")); s.map("TNotebook.Tab",background=[("selected",ACCENT)],foreground=[("selected",BG)])
        s.configure("Treeview",background=PANEL,fieldbackground=PANEL,foreground=TEXT,rowheight=34,borderwidth=0,font=("Helvetica",10)); s.configure("Treeview.Heading",background=PANEL2,foreground=ACCENT,font=("Helvetica",10,"bold")); s.map("Treeview",background=[("selected", "#24496c")])

    def _label(self,parent,text,size=10,color=TEXT,bold=False): return tk.Label(parent,text=text,bg=parent.cget("bg"),fg=color,font=("Helvetica",size,"bold" if bold else "normal"))
    def _card(self,parent): return tk.Frame(parent,bg=PANEL,highlightbackground="#263750",highlightthickness=1)
    def _button(self,parent,text,cmd,primary=False): return tk.Button(parent,text=text,command=cmd,bg=ACCENT if primary else PANEL2,fg=BG if primary else TEXT,activebackground="#8bcaff",activeforeground=BG,relief="flat",bd=0,padx=16,pady=9,font=("Helvetica",10,"bold"),cursor="hand2")

    def _build(self):
        header=tk.Frame(self,bg=BG); header.pack(fill="x",padx=26,pady=(20,12))
        tk.Label(header,text="☁  WEATHERLY",bg=BG,fg=TEXT,font=("Helvetica",22,"bold")).pack(side="left")
        self.clock=self._label(header,"",10,MUTED); self.clock.pack(side="right",pady=8)
        search=tk.Frame(self,bg=BG); search.pack(fill="x",padx=26,pady=(0,14))
        self.combo=ttk.Combobox(search,textvariable=self.city_var,width=32,values=self._saved_cities(),font=("Helvetica",12)); self.combo.pack(side="left",ipady=7); self.combo.bind("<Return>",lambda e:self.search())
        self._button(search,"Search weather",self.search,True).pack(side="left",padx=9)
        self._button(search,"☆ Favourite",self.add_favourite).pack(side="left")
        self._label(search,"Temperature",10,MUTED).pack(side="left",padx=(24,7))
        for u in ("C","F"):
            tk.Radiobutton(search,text="°"+u,variable=self.unit,value=u,command=self.render,bg=BG,fg=TEXT,selectcolor=PANEL2,activebackground=BG,activeforeground=ACCENT).pack(side="left")
        self.status=self._label(self,"Ready",9,MUTED); self.status.pack(anchor="w",padx=28,pady=(0,8))
        self.tabs=ttk.Notebook(self); self.tabs.pack(fill="both",expand=True,padx=24,pady=(0,20))
        self.dash=tk.Frame(self.tabs,bg=BG); self.planner=tk.Frame(self.tabs,bg=BG); self.tabs.add(self.dash,text="  OVERVIEW  "); self.tabs.add(self.planner,text="  WEATHER DAY PLANNER  ")
        self._build_dashboard(); self._build_planner()

    def _build_dashboard(self):
        top=tk.Frame(self.dash,bg=BG); top.pack(fill="x",pady=8)
        self.hero=self._card(top); self.hero.pack(side="left",fill="both",expand=True,padx=(0,8))
        self.city_title=self._label(self.hero,"Waiting for weather…",17,TEXT,True); self.city_title.pack(anchor="w",padx=22,pady=(18,2))
        self.condition=self._label(self.hero,"Search a city to see live conditions",11,MUTED); self.condition.pack(anchor="w",padx=22)
        row=tk.Frame(self.hero,bg=PANEL); row.pack(fill="x",padx=22,pady=14)
        self.icon_label=tk.Label(row,text="",bg=PANEL); self.icon_label.pack(side="left",padx=(0,10))
        self.temp=self._label(row,"--°",48,TEXT,True); self.temp.pack(side="left")
        self.feels=self._label(row,"Feels like --",11,MUTED); self.feels.pack(side="left",padx=18,pady=18)
        self.metrics=self._card(top); self.metrics.config(width=330); self.metrics.pack(side="right",fill="both",padx=(8,0)); self.metrics.pack_propagate(False)
        self.metric_labels=[]
        for name in ("HUMIDITY","PRESSURE","WIND SPEED","CONDITION"):
            r=tk.Frame(self.metrics,bg=PANEL); r.pack(fill="x",padx=18,pady=9)
            self._label(r,name,9,MUTED,True).pack(side="left"); v=self._label(r,"--",11,TEXT,True); v.pack(side="right"); self.metric_labels.append(v)
        section=tk.Frame(self.dash,bg=BG); section.pack(fill="both",expand=True,pady=(8,0))
        left=tk.Frame(section,bg=BG); left.pack(side="left",fill="both",expand=True,padx=(0,8))
        right=self._card(section); right.pack(side="right",fill="both",expand=True,padx=(8,0))
        self._label(left,"FIVE-DAY FORECAST",10,ACCENT,True).pack(anchor="w",pady=(4,8))
        self.forecast_table=ttk.Treeview(left,columns=("date","condition","min","max","humidity"),show="headings",height=5)
        for c,t,w in [("date","DATE",100),("condition","CONDITION",130),("min","LOW",70),("max","HIGH",70),("humidity","HUMIDITY",90)]: self.forecast_table.heading(c,text=t); self.forecast_table.column(c,width=w,anchor="center")
        self.forecast_table.pack(fill="x")
        self._label(left,"FORECAST INSIGHTS",10,ACCENT,True).pack(anchor="w",pady=(16,7))
        self.analysis=self._label(left,"Average · Min · Max · Trend will appear here",10,MUTED); self.analysis.pack(anchor="w",pady=(0,12))
        self._label(right,"TEMPERATURE TREND",10,ACCENT,True).pack(anchor="w",padx=16,pady=(12,0))
        self.chart_host=tk.Frame(right,bg=PANEL); self.chart_host.pack(fill="both",expand=True,padx=8,pady=5)
        foot=tk.Frame(self.dash,bg=BG); foot.pack(fill="x",pady=(8,0)); self._label(foot,"SEARCH HISTORY",9,MUTED,True).pack(side="left")
        self.history=tk.StringVar(value="  •  ".join(self.store.get_history()[:5]) or "No searches yet"); self._label(foot,"",9).pack(side="left"); tk.Label(foot,textvariable=self.history,bg=BG,fg=MUTED,font=("Helvetica",9)).pack(side="left",padx=12)
        self._button(foot,"Refresh now",self.search).pack(side="right")

    def _build_planner(self):
        tk.Label(self.planner,text="PLAN YOUR DAY AROUND THE WEATHER",bg=BG,fg=TEXT,font=("Helvetica",17,"bold")).pack(anchor="w",padx=20,pady=(18,4))
        tk.Label(self.planner,text="Add an activity and Weatherly will compare it with the forecast for that day.",bg=BG,fg=MUTED,font=("Helvetica",10)).pack(anchor="w",padx=20,pady=(0,16))
        form=self._card(self.planner); form.pack(fill="x",padx=20,pady=4)
        fields=tk.Frame(form,bg=PANEL); fields.pack(fill="x",padx=16,pady=14)
        self.activity=tk.StringVar(); self.plan_date=tk.StringVar(value=date.today().isoformat()); self.plan_time=tk.StringVar(value="08:00"); self.outdoor=tk.BooleanVar(value=True)
        for col,(label,var,width) in enumerate([("ACTIVITY",self.activity,22),("DATE (YYYY-MM-DD)",self.plan_date,14),("TIME (24H)",self.plan_time,10)]):
            box=tk.Frame(fields,bg=PANEL); box.grid(row=0,column=col,padx=(0,12),sticky="w"); self._label(box,label,9,MUTED,True).pack(anchor="w"); tk.Entry(box,textvariable=var,width=width,bg="#0d1829",fg=TEXT,insertbackground=TEXT,relief="flat",font=("Helvetica",11)).pack(ipady=8,pady=5)
        tk.Checkbutton(fields,text="Outdoor activity",variable=self.outdoor,bg=PANEL,fg=TEXT,selectcolor=PANEL2,activebackground=PANEL).grid(row=0,column=3,padx=10)
        self._button(fields,"＋ Add activity",self.add_activity,True).grid(row=0,column=4,padx=8)
        self.plan_table=ttk.Treeview(self.planner,columns=("activity","date","time","type"),show="headings",height=9)
        for c,t,w in [("activity","ACTIVITY",360),("date","DATE",160),("time","TIME",120),("type","SETTING",160)]: self.plan_table.heading(c,text=t); self.plan_table.column(c,width=w,anchor="center")
        self.plan_table.pack(fill="both",expand=True,padx=20,pady=14)
        actions=tk.Frame(self.planner,bg=BG); actions.pack(fill="x",padx=20); self._button(actions,"Delete selected",self.delete_activity).pack(side="left"); self._button(actions,"Check selected against forecast",self.check_activity,True).pack(side="left",padx=10)
        self.plan_status=tk.Label(self.planner,text="Weather checks use the five-day forecast. Keep the app open for reminders.",bg=BG,fg=MUTED,font=("Helvetica",9)); self.plan_status.pack(anchor="w",padx=20,pady=10)
        self._load_plans()

    def _saved_cities(self): return list(dict.fromkeys(self.store.get_favourites()+self.store.get_history()))
    def search(self):
        city=self.city_var.get().strip()
        if not city: messagebox.showwarning("City required","Please enter a city name."); return
        self.status.config(text="Fetching live weather…"); threading.Thread(target=self._worker,args=(city,),daemon=True).start()
    def _worker(self,city):
        try:
            current=self.client.fetch_current(city); forecast=self.client.fetch_forecast(city); icon=self.client.fetch_icon(current.icon)
            self.results.put(("ok",current,forecast,icon))
        except WeatherError as e: self.results.put(("error",str(e)))
        except Exception as e: self.results.put(("error",f"Unexpected error: {e}"))
    def _poll_results(self):
        try:
            while True:
                msg=self.results.get_nowait()
                if msg[0]=="ok":
                    self.current,self.forecast,self.weather_icon=msg[1],msg[2],msg[3]; self.store.add_history(self.current.city); self.combo["values"]=self._saved_cities(); self.history.set("  •  ".join(self.store.get_history()[:5])); self.status.config(text="Updated successfully · OpenWeatherMap"); self.render()
                else: self.status.config(text="Could not update weather"); messagebox.showerror("Weather error",msg[1])
        except queue.Empty: pass
        self.after(200,self._poll_results)
    def _temp(self,c): return self.current.convert(c,self.unit.get())
    def render(self):
        if not self.current:return
        u=self.unit.get(); self.city_title.config(text=f"{self.current.city}, {self.current.country}"); self.icon_photo=ImageTk.PhotoImage(self.weather_icon.resize((76,76))) if self.weather_icon else None; self.icon_label.config(image=self.icon_photo if self.icon_photo else "", text="" if self.icon_photo else "☁", fg=TEXT, font=("Helvetica",30)); self.condition.config(text=self.current.condition); self.temp.config(text=f"{self._temp(self.current.temp_c):.1f}°{u}"); self.feels.config(text=f"Feels like {self._temp(self.current.feels_like_c):.1f}°{u}")
        vals=[f"{self.current.humidity}%",f"{self.current.pressure} hPa",f"{self.current.wind_speed:.1f} m/s",self.current.condition]
        for label,val in zip(self.metric_labels,vals): label.config(text=val)
        for item in self.forecast_table.get_children(): self.forecast_table.delete(item)
        for d in self.forecast:
            self.forecast_table.insert("","end",values=(datetime.strptime(d.date,"%Y-%m-%d").strftime("%a, %d %b"),d.condition,f"{self._temp(d.temp_min_c):.1f}°",f"{self._temp(d.temp_max_c):.1f}°",f"{d.humidity}%"))
        self.analysis.config(text=WeatherAnalyzer(self.forecast).summary().replace("°C",f"°{u}") if u=="C" else self._analysis_f())
        for w in self.chart_host.winfo_children():w.destroy()
        fig=ChartPlotter.build_figure(self.forecast,u); fig.patch.set_facecolor(PANEL); ax=fig.axes[0]; ax.set_facecolor(PANEL); ax.tick_params(colors=MUTED); ax.yaxis.label.set_color(MUTED); ax.xaxis.label.set_color(MUTED)
        for sp in ax.spines.values():sp.set_color("#33445e")
        canvas=FigureCanvasTkAgg(fig,master=self.chart_host); canvas.draw(); canvas.get_tk_widget().pack(fill="both",expand=True)
    def _analysis_f(self):
        a=WeatherAnalyzer(self.forecast); return f"5-day average {self._temp(a.average()):.1f}°F   •   Min {self._temp(a.minimum()):.1f}°F   •   Max {self._temp(a.maximum()):.1f}°F   •   {a.trend()} trend"
    def add_favourite(self):
        if not self.current: messagebox.showinfo("Favourite","Search a city first."); return
        self.store.add_favourite(self.current.city); self.combo["values"]=self._saved_cities(); messagebox.showinfo("Saved",f"{self.current.city} added to favourites.")
    def _clock(self): self.clock.config(text=datetime.now().strftime("%A, %d %B %Y   •   %I:%M:%S %p")); self.after(1000,self._clock)
    def _auto_refresh(self):
        if self.current and not self.results.qsize(): threading.Thread(target=self._worker,args=(self.current.city,),daemon=True).start()
        self.after(max(60,int(CONFIG.get("refresh_seconds",600)))*1000,self._auto_refresh)

    # Additional weather-aware planner (requested extension)
    @property
    def plans_file(self): return ROOT/"data"/"schedule.json"
    def _plans(self):
        try:return json.loads(self.plans_file.read_text())
        except Exception:return []
    def _save_plans(self,p): self.plans_file.write_text(json.dumps(p,indent=2))
    def _load_plans(self):
        for x in self._plans(): self.plan_table.insert("","end",iid=x["id"],values=(x["activity"],x["date"],x["time"],"Outdoor" if x["outdoor"] else "Indoor"))
    def add_activity(self):
        try:
            name=self.activity.get().strip(); datetime.strptime(self.plan_date.get(),"%Y-%m-%d"); datetime.strptime(self.plan_time.get(),"%H:%M")
            if not name: raise ValueError("Enter an activity name.")
            import uuid
            item={"id":uuid.uuid4().hex[:10],"activity":name,"date":self.plan_date.get(),"time":self.plan_time.get(),"outdoor":self.outdoor.get()}
            p=self._plans(); p.append(item); self._save_plans(p); self.plan_table.insert("","end",iid=item["id"],values=(name,item["date"],item["time"],"Outdoor" if item["outdoor"] else "Indoor")); self.activity.set(""); self.plan_status.config(text="Activity saved. Select it and check the forecast for weather advice.")
        except ValueError as e: messagebox.showerror("Invalid schedule",str(e))
    def delete_activity(self):
        sel=self.plan_table.selection()
        if not sel:return
        ids=set(sel); self._save_plans([p for p in self._plans() if p["id"] not in ids])
        for i in ids:self.plan_table.delete(i)
    def _schedule_alerts(self):
        """Show a one-time reminder within 30 minutes of a planned activity."""
        now=datetime.now()
        for p in self._plans():
            if p["id"] in self.alerted: continue
            try: when=datetime.strptime(p["date"]+" "+p["time"],"%Y-%m-%d %H:%M")
            except ValueError: continue
            minutes=(when-now).total_seconds()/60
            if 0 < minutes <= 30:
                self.alerted.add(p["id"])
                note=f"{p['activity']} starts in about {int(minutes)} minutes."
                day=next((d for d in self.forecast if d.date==p["date"]),None)
                if p["outdoor"] and day:
                    cond=day.condition.lower()
                    if any(k in cond for k in ("rain","storm","thunder","snow","drizzle")):
                        note += f"\nWeather warning: {day.condition} expected. Consider rescheduling or moving indoors."
                    elif day.temp_max_c>=34:
                        note += f"\nHeat warning: forecast high is {day.temp_max_c:.1f}°C."
                    else: note += f"\nForecast: {day.condition}, high {day.temp_max_c:.1f}°C."
                messagebox.showwarning("Upcoming activity",note)
        self.after(30000,self._schedule_alerts)

    def check_activity(self):
        sel=self.plan_table.selection()
        if not sel:messagebox.showinfo("Select activity","Select an activity first.");return
        p=next((x for x in self._plans() if x["id"]==sel[0]),None)
        if not p:return
        if not self.forecast:messagebox.showwarning("Forecast unavailable","Search a city first to load its forecast.");return
        day=next((d for d in self.forecast if d.date==p["date"]),None)
        if not day:messagebox.showinfo("Outside forecast", "This activity is outside the currently available five-day forecast.");return
        condition=day.condition.lower(); bad=any(k in condition for k in ("rain","storm","thunder","snow","drizzle"))
        hot=day.temp_max_c>=34
        advice="Weather looks suitable based on the available forecast."
        if p["outdoor"] and bad:advice=f"Weather warning: {day.condition} is forecast. Consider moving {p['activity']} indoors or rescheduling."
        elif p["outdoor"] and hot:advice=f"High temperature expected (up to {day.temp_max_c:.1f}°C). Avoid peak heat and stay hydrated."
        elif not p["outdoor"]:advice="Indoor activity: no weather-related change is usually needed."
        messagebox.showinfo(f"Weather check · {p['activity']}",f"{p['date']} at {p['time']}\nForecast: {day.condition}\nLow / high: {day.temp_min_c:.1f}°C / {day.temp_max_c:.1f}°C\n\n{advice}")

if __name__=="__main__": WeatherApp().mainloop()
