"""ReportGenerator — Jinja2-based HTML report generation with matplotlib charts."""

import io
import base64
import os
from jinja2 import Environment, FileSystemLoader
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


class ReportGenerator:
    _template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    _env = Environment(loader=FileSystemLoader(_template_dir))

    @classmethod
    def generate_hole_report(cls, summary: dict, fill_stats: list,
                             effect: dict, info: dict) -> str:
        charts = cls._generate_hole_charts(summary.get("diameters", []))
        size_dist = cls._build_size_dist_table(summary.get("size_distribution", {}),
                                               summary.get("total_count", 0))
        template = cls._env.get_template("hole_report.html")
        html = template.render(
            info=info,
            summary={
                "total_count": summary["total_count"],
                "total_area_mm2": summary["total_area_mm2"],
                "avg_area_mm2": summary["avg_area_mm2"],
                "porosity_percent": summary["porosity_percent"],
                "avg_d_mm": summary["avg_equivalent_d_mm"],
                "max_d_mm": summary["max_equivalent_d_mm"],
                "min_d_mm": summary["min_equivalent_d_mm"],
            },
            fill_stats=fill_stats,
            effect=effect,
            size_dist=size_dist,
            charts=charts
        )
        return html

    @classmethod
    def generate_fracture_report(cls, summary: dict, fractures: list,
                                 type_stats: list, info: dict) -> str:
        template = cls._env.get_template("fracture_report.html")
        html = template.render(info=info, summary=summary,
                               fractures=fractures, type_stats=type_stats)
        return html

    @classmethod
    def _generate_hole_charts(cls, diameters: list) -> dict:
        if not diameters:
            return {"histogram": "", "cumulative": "", "normal_cdf": ""}
        diameters = np.array(diameters)
        charts = {}

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(diameters, bins=min(10, len(diameters)), edgecolor='black', alpha=0.7)
        ax.set_xlabel("等效直径 (mm)")
        ax.set_ylabel("频数")
        ax.set_title("孔洞等效直径频率直方图")
        charts["histogram"] = cls._fig_to_b64(fig)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 4))
        sorted_d = np.sort(diameters)
        cumulative = np.arange(1, len(sorted_d) + 1) / len(sorted_d) * 100
        ax.plot(sorted_d, cumulative, 'b-o', markersize=4)
        ax.set_xlabel("等效直径 (mm)")
        ax.set_ylabel("累计频率 (%)")
        ax.set_title("孔洞等效直径累计频率曲线")
        charts["cumulative"] = cls._fig_to_b64(fig)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 4))
        mu, sigma = np.mean(diameters), np.std(diameters)
        if sigma > 0:
            x = np.linspace(max(0, mu - 3 * sigma), mu + 3 * sigma, 100)
            ax.plot(x, stats.norm.cdf(x, mu, sigma) * 100, 'r-', lw=2, label=f"μ={mu:.2f}, σ={sigma:.2f}")
            ax.scatter(sorted_d, cumulative, s=10, alpha=0.5, label="实测")
            ax.legend()
        ax.set_xlabel("等效直径 (mm)")
        ax.set_ylabel("累计概率 (%)")
        ax.set_title("孔洞等效直径正态累计曲线")
        charts["normal_cdf"] = cls._fig_to_b64(fig)
        plt.close(fig)
        return charts

    @staticmethod
    def _fig_to_b64(fig) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()

    @staticmethod
    def _build_size_dist_table(size_dist: dict, total: int) -> list:
        ranges = {"大洞": ">10mm", "中洞": "5-10mm", "小洞": "1-4.9mm", "针孔/溶孔": "<1mm"}
        return [{"category": k, "range": ranges.get(k, ""),
                 "count": size_dist.get(k, 0),
                 "percent": round(size_dist.get(k, 0) / total * 100, 1) if total > 0 else 0}
                for k in ("大洞", "中洞", "小洞", "针孔/溶孔")]
