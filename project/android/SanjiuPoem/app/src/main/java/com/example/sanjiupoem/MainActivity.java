package com.example.sanjiupoem;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

/**
 * 三元九爻 · 年龄分类诗词 —— 图文并茂界面。
 * 用自定义 GuaView 把三元卦象画成"卦画"：阳爻实线、阴爻断线、中和爻中菱形；
 * 诗歌卡片化，每首配小卦象图 + 象义。古典配色：米白底/墨字/朱砂/松花绿。
 */
public class MainActivity extends Activity {

    // 古典配色
    private static final int BG = 0xFFF6F1E7;      // 米白
    private static final int CARD = 0xFFFFFFFF;
    private static final int INK = 0xFF26221C;     // 墨
    private static final int ACCENT = 0xFFB5432A;  // 朱砂
    private static final int GREEN = 0xFF3E5C46;   // 松花绿
    private static final int GRAY = 0xFF8A8274;
    private static final int BORDER = 0xFFE4DCCA;

    private List<SanjiuEngine.Poem> poems = new ArrayList<>();
    private List<SanjiuEngine.OrigPoem> origPoems = new ArrayList<>();
    private LinearLayout cardArea;          // 诗歌卡片区
    private GuaView bigGua;                 // 当前目标卦大图
    private TextView bigOracle, bigCaption;
    private int currentAge = 0;
    private boolean originalMode = false;
    private final Button[] ageChips = new Button[5];

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // 根：整页可滚
        ScrollView page = new ScrollView(this);
        page.setBackgroundColor(BG);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(20), dp(24), dp(20), dp(30));
        page.addView(root);

        // ---- 标题 ----
        TextView title = new TextView(this);
        title.setText("三元九爻 · 年龄分类诗词");
        title.setTextSize(24f);
        title.setTextColor(INK);
        title.setTypeface(title.getTypeface(), android.graphics.Typeface.BOLD);
        root.addView(title);
        TextView sub = new TextView(this);
        sub.setText("以 9 维诗卦（主旨·情感·意象·用典·音律·修辞·意脉·境界·立意）推演分类，选年龄段即成篇。");
        sub.setTextSize(13f);
        sub.setTextColor(GRAY);
        sub.setPadding(0, dp(4), 0, dp(14));
        root.addView(sub);

        // ---- 图例 ----
        root.addView(buildLegend());

        // ---- 当前目标卦大图 ----
        LinearLayout hero = new LinearLayout(this);
        hero.setOrientation(LinearLayout.HORIZONTAL);
        hero.setBackground(round(0xFFFFFFFF, dp(14), dp(1), BORDER));
        hero.setPadding(dp(16), dp(12), dp(16), dp(12));
        bigGua = new GuaView(this);
        bigGua.setMinimumHeight(dp(210));
        bigGua.setMinimumWidth(dp(96));
        hero.addView(bigGua, new LinearLayout.LayoutParams(dp(96), dp(210)));
        LinearLayout heroTxt = new LinearLayout(this);
        heroTxt.setOrientation(LinearLayout.VERTICAL);
        heroTxt.setPadding(dp(12), 0, 0, 0);
        bigCaption = new TextView(this);
        bigCaption.setTextSize(17f);
        bigCaption.setTextColor(ACCENT);
        bigCaption.setTypeface(bigCaption.getTypeface(), android.graphics.Typeface.BOLD);
        bigOracle = new TextView(this);
        bigOracle.setTextSize(13f);
        bigOracle.setTextColor(INK);
        bigOracle.setLineSpacing(dp(2), 1f);
        heroTxt.addView(bigCaption);
        heroTxt.addView(bigOracle);
        hero.addView(heroTxt, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1f));
        root.addView(hero);

        root.addView(space(dp(14)));

        // ---- 年龄段 chip 选择 ----
        HorizontalScrollView hsv = new HorizontalScrollView(this);
        hsv.setHorizontalScrollBarEnabled(false);
        LinearLayout chipRow = new LinearLayout(this);
        chipRow.setOrientation(LinearLayout.HORIZONTAL);
        String[] names = SanjiuEngine.AGE_NAMES;
        for (int i = 0; i < names.length; i++) {
            final int idx = i;
            Button chip = new Button(this);
            chip.setText(names[i]);
            chip.setAllCaps(false);
            chip.setTextSize(15f);
            chip.setPadding(dp(18), dp(8), dp(18), dp(8));
            ageChips[i] = chip;
            chip.setOnClickListener(v -> { currentAge = idx; refresh(); });
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
            lp.setMargins(0, 0, dp(10), 0);
            chipRow.addView(chip, lp);
        }
        hsv.addView(chipRow);
        root.addView(hsv);
        root.addView(space(dp(12)));

        // ---- 操作按钮 ----
        Button evolve = new Button(this);
        evolve.setText("⇄ 三元推演（错 / 综 / 错综 / 变爻）");
        evolve.setTextColor(0xFFFFFFFF);
        evolve.setBackground(round(ACCENT, dp(10), 0, 0));
        evolve.setOnClickListener(v -> renderEvolved());
        root.addView(evolve);
        root.addView(space(dp(12)));

        // ---- 模式切换：经典分类 / 三元原创 ----
        Button modeBtn = new Button(this);
        modeBtn.setText("三元原创 · 看本年龄段创作诗");
        modeBtn.setTextColor(GREEN);
        modeBtn.setBackground(round(0xFFFBF7EE, dp(10), dp(1), BORDER));
        modeBtn.setOnClickListener(v -> {
            originalMode = !originalMode;
            modeBtn.setText(originalMode
                    ? "经典分类 · 回诗卦最近者"
                    : "三元原创 · 看本年龄段创作诗");
            refresh();
        });
        root.addView(modeBtn);
        root.addView(space(dp(16)));

        // ---- 卡片区 ----
        cardArea = new LinearLayout(this);
        cardArea.setOrientation(LinearLayout.VERTICAL);
        root.addView(cardArea);

        setContentView(page);

        // 加载语料
        try {
            InputStream is = getAssets().open("poems.json");
            byte[] buf = new byte[is.available()];
            is.read(buf);
            is.close();
            poems = SanjiuEngine.load(new JSONArray(new String(buf, "UTF-8")));
            InputStream is2 = getAssets().open("original.json");
            byte[] buf2 = new byte[is2.available()];
            is2.read(buf2);
            is2.close();
            origPoems = SanjiuEngine.loadOrig(new JSONArray(new String(buf2, "UTF-8")));
        } catch (Exception e) {
            poems = new ArrayList<>();
            origPoems = new ArrayList<>();
        }
        refresh();
    }

    private void refresh() {
        for (int i = 0; i < ageChips.length; i++) {
            ageChips[i].setTextColor(i == currentAge ? 0xFFFFFFFF : INK);
            ageChips[i].setBackground(round(i == currentAge ? ACCENT : CARD,
                    dp(18), dp(1), i == currentAge ? ACCENT : BORDER));
        }
        int[] target = SanjiuEngine.AGE_GUA[currentAge];
        bigGua.setGua(target);
        bigCaption.setText(SanjiuEngine.AGE_NAMES[currentAge] + " · 风格卦");
        bigOracle.setText(SanjiuEngine.oracle(target));
        render();
    }

    private void render() {
        if (originalMode) renderOriginal();
        else renderClassified();
    }

    // 三元原创：本年龄段的 4 首创作诗
    private void renderOriginal() {
        cardArea.removeAllViews();
        cardArea.addView(sectionLabel("「" + SanjiuEngine.AGE_NAMES[currentAge] + "」三元原创 · 诗卦驱动的创作诗"));
        for (SanjiuEngine.OrigPoem p : SanjiuEngine.origByAge(origPoems, currentAge)) {
            cardArea.addView(origCard(p));
            cardArea.addView(space(dp(12)));
        }
    }

    // 原创诗卡片
    private View origCard(SanjiuEngine.OrigPoem p) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackground(round(CARD, dp(14), dp(1), BORDER));
        card.setPadding(dp(14), dp(12), dp(14), dp(14));
        LinearLayout head = new LinearLayout(this);
        head.setOrientation(LinearLayout.HORIZONTAL);
        head.setGravity(Gravity.CENTER_VERTICAL);
        GuaView mini = new GuaView(this);
        mini.setMinimumHeight(dp(78));
        mini.setMinimumWidth(dp(36));
        mini.setGua(p.gua);
        head.addView(mini, new LinearLayout.LayoutParams(dp(36), dp(78)));
        LinearLayout txt = new LinearLayout(this);
        txt.setOrientation(LinearLayout.VERTICAL);
        txt.setPadding(dp(10), 0, 0, 0);
        TextView ht = new TextView(this);
        ht.setText("《" + p.title + "》· " + p.op);
        ht.setTextSize(16f);
        ht.setTextColor(INK);
        ht.setTypeface(ht.getTypeface(), android.graphics.Typeface.BOLD);
        txt.addView(ht);
        TextView tag = new TextView(this);
        tag.setText("三元原创");
        tag.setTextSize(12f);
        tag.setTextColor(0xFFFFFFFF);
        tag.setPadding(dp(6), dp(2), dp(6), dp(2));
        tag.setBackground(round(GREEN, dp(8), 0, 0));
        txt.addView(tag);
        head.addView(txt, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));
        card.addView(head);
        TextView body = new TextView(this);
        body.setText(p.text);
        body.setTextSize(15f);
        body.setTextColor(INK);
        body.setLineSpacing(dp(4), 1.12f);
        body.setPadding(0, dp(10), 0, dp(6));
        card.addView(body);
        // 正轨专业解读（人类传统诗评语言）
        if (p.interpretation != null && !p.interpretation.isEmpty()) {
            card.addView(space(dp(2)));
            TextView interLabel = new TextView(this);
            interLabel.setText("解 读");
            interLabel.setTextSize(12f);
            interLabel.setTextColor(0xFFFFFFFF);
            interLabel.setPadding(dp(6), dp(2), dp(6), dp(2));
            interLabel.setBackground(round(ACCENT, dp(8), 0, 0));
            card.addView(interLabel);
            TextView inter = new TextView(this);
            inter.setText(p.interpretation);
            inter.setTextSize(13f);
            inter.setTextColor(INK);
            inter.setLineSpacing(dp(2), 1.14f);
            inter.setPadding(0, dp(6), 0, dp(8));
            card.addView(inter);
        }
        TextView meta = new TextView(this);
        meta.setText("创作卦 " + toStr(p.gua) + "\n" + p.oracle
                + "\n解读坐标：" + SanjiuEngine.coordinate(p.gua));
        meta.setTextSize(11f);
        meta.setTextColor(GRAY);
        card.addView(meta);
        return card;
    }

    // 年龄段分类诗歌卡片
    private void renderClassified() {
        cardArea.removeAllViews();
        cardArea.addView(sectionLabel("「" + SanjiuEngine.AGE_NAMES[currentAge] + "」分类 · 诗卦最近者"));
        int[] target = SanjiuEngine.AGE_GUA[currentAge];
        for (SanjiuEngine.Poem p : SanjiuEngine.classify(poems, currentAge, 4)) {
            cardArea.addView(poemCard(p, target));
            cardArea.addView(space(dp(12)));
        }
    }

    // 三元推演结果卡片
    private void renderEvolved() {
        cardArea.removeAllViews();
        cardArea.addView(sectionLabel("「" + SanjiuEngine.AGE_NAMES[currentAge] + "」三元推演 · 衍生卦检索全库"));
        for (int[] t : SanjiuEngine.deriveTargets(currentAge, 3)) {
            SanjiuEngine.Poem best = null;
            double bestD = Double.MAX_VALUE;
            for (SanjiuEngine.Poem p : poems) {
                double d = SanjiuEngine.dist(t, p.gua);
                if (d < bestD) { bestD = d; best = p; }
            }
            cardArea.addView(evolveCard(t, best, bestD));
            cardArea.addView(space(dp(12)));
        }
    }

    // ---- 组件构造 ----
    private View buildLegend() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, 0, 0, dp(10));
        row.addView(legendCell(1, "阳·显"));
        row.addView(legendCell(-1, "阴·隐"));
        row.addView(legendCell(0, "中和·衡"));
        return row;
    }

    private View legendCell(int v, String label) {
        LinearLayout cell = new LinearLayout(this);
        cell.setOrientation(LinearLayout.VERTICAL);
        cell.setGravity(Gravity.CENTER);
        cell.setPadding(dp(10), 0, dp(10), 0);
        GuaView mini = new GuaView(this);
        mini.setLineColor(ACCENT);
        mini.setMinimumWidth(dp(40));
        mini.setMinimumHeight(dp(34));
        mini.setGua(new int[]{v, 0, 0, 0, 0, 0, 0, 0, 0});
        cell.addView(mini, new LinearLayout.LayoutParams(dp(40), dp(34)));
        TextView t = new TextView(this);
        t.setText(label);
        t.setTextSize(11f);
        t.setTextColor(GRAY);
        cell.addView(t);
        return cell;
    }

    private View sectionLabel(String s) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(15f);
        t.setTextColor(GREEN);
        t.setTypeface(t.getTypeface(), android.graphics.Typeface.BOLD);
        t.setPadding(0, 0, 0, dp(10));
        return t;
    }

    private View poemCard(SanjiuEngine.Poem p, int[] target) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackground(round(CARD, dp(14), dp(1), BORDER));
        card.setPadding(dp(14), dp(12), dp(14), dp(14));

        // 顶行：小卦象图 + 标题/作者 + 主题标签
        LinearLayout head = new LinearLayout(this);
        head.setOrientation(LinearLayout.HORIZONTAL);
        head.setGravity(Gravity.CENTER_VERTICAL);
        GuaView mini = new GuaView(this);
        mini.setMinimumHeight(dp(78));
        mini.setMinimumWidth(dp(36));
        mini.setGua(p.gua);
        head.addView(mini, new LinearLayout.LayoutParams(dp(36), dp(78)));
        LinearLayout txt = new LinearLayout(this);
        txt.setOrientation(LinearLayout.VERTICAL);
        txt.setPadding(dp(10), 0, 0, 0);
        TextView ht = new TextView(this);
        ht.setText("《" + p.title + "》·" + p.author);
        ht.setTextSize(16f);
        ht.setTextColor(INK);
        ht.setTypeface(ht.getTypeface(), android.graphics.Typeface.BOLD);
        txt.addView(ht);
        TextView tag = new TextView(this);
        tag.setText(SanjiuEngine.AGE_NAMES[p.age] + " · " + p.topic);
        tag.setTextSize(12f);
        tag.setTextColor(ACCENT);
        tag.setPadding(dp(6), dp(2), dp(6), dp(2));
        tag.setBackground(round(0xFFF4E3D7, dp(8), 0, 0));
        txt.addView(tag);
        txt.addView(space(dp(2)));
        head.addView(txt, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));
        card.addView(head);

        // 正文
        TextView body = new TextView(this);
        body.setText(p.text);
        body.setTextSize(15f);
        body.setTextColor(INK);
        body.setLineSpacing(dp(4), 1.12f);
        body.setPadding(0, dp(10), 0, dp(6));
        card.addView(body);

        // 正轨专业导读（人类传统诗评语言）
        if (p.interpretation != null && !p.interpretation.isEmpty()) {
            card.addView(space(dp(2)));
            TextView interLabel = new TextView(this);
            interLabel.setText("导 读");
            interLabel.setTextSize(12f);
            interLabel.setTextColor(0xFFFFFFFF);
            interLabel.setPadding(dp(6), dp(2), dp(6), dp(2));
            interLabel.setBackground(round(ACCENT, dp(8), 0, 0));
            card.addView(interLabel);
            TextView inter = new TextView(this);
            inter.setText(p.interpretation);
            inter.setTextSize(13f);
            inter.setTextColor(INK);
            inter.setLineSpacing(dp(2), 1.14f);
            inter.setPadding(0, dp(6), 0, dp(8));
            card.addView(inter);
        }

        // 象义 / 距离
        TextView meta = new TextView(this);
        meta.setText("诗卦 " + toStr(p.gua) + " · 距风格卦 "
                + String.format("%.2f", SanjiuEngine.dist(target, p.gua))
                + "\n" + SanjiuEngine.oracle(p.gua)
                + "\n解读坐标：" + SanjiuEngine.coordinate(p.gua));
        meta.setTextSize(11f);
        meta.setTextColor(GRAY);
        card.addView(meta);
        return card;
    }

    private View evolveCard(int[] t, SanjiuEngine.Poem best, double d) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackground(round(0xFFFBF7EE, dp(14), dp(1), BORDER));
        card.setPadding(dp(14), dp(12), dp(14), dp(12));
        LinearLayout head = new LinearLayout(this);
        head.setOrientation(LinearLayout.HORIZONTAL);
        head.setGravity(Gravity.CENTER_VERTICAL);
        GuaView mini = new GuaView(this);
        mini.setMinimumHeight(dp(78));
        mini.setMinimumWidth(dp(36));
        mini.setGua(t);
        head.addView(mini, new LinearLayout.LayoutParams(dp(36), dp(78)));
        LinearLayout txt = new LinearLayout(this);
        txt.setOrientation(LinearLayout.VERTICAL);
        txt.setPadding(dp(10), 0, 0, 0);
        TextView or = new TextView(this);
        or.setText(SanjiuEngine.oracle(t));
        or.setTextSize(12f);
        or.setTextColor(INK);
        txt.addView(or);
        if (best != null) {
            TextView hit = new TextView(this);
            hit.setText("→ 《" + best.title + "》·" + best.author + "  ["
                    + SanjiuEngine.AGE_NAMES[best.age] + "·" + best.topic + "] 距 "
                    + String.format("%.2f", d));
            hit.setTextSize(13f);
            hit.setTextColor(GREEN);
            hit.setTypeface(hit.getTypeface(), android.graphics.Typeface.BOLD);
            txt.addView(hit);
        }
        head.addView(txt, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));
        card.addView(head);
        if (best != null) {
            TextView body = new TextView(this);
            body.setText(best.text);
            body.setTextSize(14f);
            body.setTextColor(INK);
            body.setPadding(0, dp(8), 0, 0);
            card.addView(body);
        }
        return card;
    }

    private View space(int h) {
        View v = new View(this);
        v.setMinimumHeight(h);
        return v;
    }

    private GradientDrawable round(int color, int radius, int strokeW, int strokeC) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(radius);
        if (strokeW > 0) g.setStroke(strokeW, strokeC);
        return g;
    }

    private int dp(float d) {
        return (int) (d * getResources().getDisplayMetrics().density);
    }

    private static String toStr(int[] g) {
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < g.length; i++) {
            sb.append(g[i] > 0 ? "+" : "").append(g[i]);
            if (i < g.length - 1) sb.append(",");
        }
        return sb.append("]").toString();
    }

    // ---------------- 三元卦象图（自定义 View） ----------------
    public static class GuaView extends View {
        private int[] g = new int[9];
        private int lineColor = 0xFF26221C;

        public GuaView(Context c) { super(c); }

        public void setGua(int[] gua) { g = gua; invalidate(); }
        public void setLineColor(int c) { lineColor = c; }
        private float dp(float d) { return d * getResources().getDisplayMetrics().density; }

        @Override
        protected void onDraw(Canvas cv) {
            if (g == null) return;
            Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
            p.setColor(lineColor);
            float w = getWidth();
            float h = getHeight();
            float padL = dp(3), padR = dp(3);
            float rowH = h / 9f;
            for (int i = 0; i < 9; i++) {
                float cy = i * rowH + rowH / 2f;
                float th = Math.max(2f, rowH * 0.30f);
                int v = g[i];
                if (v == 1) {                       // 阳爻：实线
                    cv.drawRect(padL, cy - th / 2, w - padR, cy + th / 2, p);
                } else if (v == -1) {               // 阴爻：断线
                    float seg = (w - padL - padR - (w - padL - padR) / 3f) / 2f;
                    cv.drawRect(padL, cy - th / 2, padL + seg, cy + th / 2, p);
                    cv.drawRect(w - padR - seg, cy - th / 2, w - padR, cy + th / 2, p);
                } else {                            // 中和爻：细线 + 中菱形（势能点）
                    p.setStrokeWidth(Math.max(1.5f, th * 0.22f));
                    cv.drawLine(padL, cy, w - padR, cy, p);
                    Path d = new Path();
                    float s = th * 0.9f, cx = w / 2f;
                    d.moveTo(cx, cy - s);
                    d.lineTo(cx + s, cy);
                    d.lineTo(cx, cy + s);
                    d.lineTo(cx - s, cy);
                    d.close();
                    cv.drawPath(d, p);
                    p.setStrokeWidth(0);
                }
            }
        }
    }
}
