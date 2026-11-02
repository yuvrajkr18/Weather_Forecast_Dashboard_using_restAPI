from matplotlib.figure import Figure
class ChartPlotter:
    @staticmethod
    def build_figure(days, unit="C"):
        fig=Figure(figsize=(7.4,2.5),dpi=100); ax=fig.add_subplot(111)
        labels=[d.date[5:] for d in days]
        lo=[d.temp_min_c for d in days]; hi=[d.temp_max_c for d in days]
        if unit=="F": lo=[x*9/5+32 for x in lo]; hi=[x*9/5+32 for x in hi]
        ax.plot(labels,hi,marker="o",linewidth=2,label="Maximum")
        ax.plot(labels,lo,marker="o",linewidth=2,label="Minimum")
        ax.fill_between(labels,lo,hi,alpha=.12)
        ax.set_ylabel("Temperature (°"+unit+")"); ax.grid(alpha=.2); ax.legend(frameon=False,ncol=2,loc="upper right")
        fig.tight_layout(); return fig
