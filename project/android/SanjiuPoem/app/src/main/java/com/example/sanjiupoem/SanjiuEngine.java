package com.example.sanjiupoem;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * 三元九爻 · 诗歌引擎。
 *
 * 把三元九爻公理（阳+1/中和0/阴-1，9维）迁移到"诗维"：
 * 9 爻位 = 主旨显隐/情感强度/意象虚实/用典深浅/音律平仄/修辞张力/意脉通滞/境界显晦/立意根基。
 * 每个年龄段给一个风格卦；每首诗给一个风格卦（由主题映射）。分类检索 = 目标卦
 * 与诗卦的欧氏距离 Top-N；并用错/综/互/变算子做推演（三元变爻生成衍生卦）。
 * 本类是 APK 内的独立实现，不依赖外部服务，纯本地计算。
 */
public class SanjiuEngine {

    // 爻态：+1 阳（显/外/生），0 中和（中/蓄/衡），-1 阴（隐/内/收）
    public static final String[] AXIS = {
        "主旨显隐", "情感强度", "意象虚实", "用典深浅", "音律平仄",
        "修辞张力", "意脉通滞", "境界显晦", "立意根基"
    };
    // 每爻位意象词（阳, 阴）；中和 → "中和持衡"
    private static final String[][] IMG = {
        {"显豁", "深隐"}, {"浓烈", "含蓄"}, {"具象", "虚淡"},
        {"白描", "典重"}, {"谐畅", "拗涩"}, {"张力", "舒缓"},
        {"贯通", "滞碍"}, {"朗照", "幽晦"}, {"根深", "浮薄"},
    };

    public static final String[] AGE_NAMES = {"儿童", "少年", "青年", "中年", "老年"};
    // 年龄段风格卦（9维偏好向量）
    public static final int[][] AGE_GUA = {
        { 1, 1, 1, -1, 0, 1, 1, 1, 1},   // 儿童：显/浓/实/无典/谐畅/有张力/贯通/朗照/根深
        { 1, 1, 0,  0, 0, 1, 1, 0, 0},   // 少年：励志进取
        { 0, 1, 1,  0, 0, 0, 1, -1, 0},  // 青年：情思婉转
        { 0, 0, -1, 1, 0, 0, 0, 0, 1},   // 中年：哲理厚重
        {-1, 0, -1, 1, 0, -1, -1, 0, 1}, // 老年：沉静思辨
    };

    // ---------------- 三元算子（公理迁移） ----------------
    public static int[] fc(int[] g) {          // 错卦：逐爻取反
        int[] r = new int[9];
        for (int i = 0; i < 9; i++) r[i] = -g[i];
        return r;
    }
    public static int[] fz(int[] g) {          // 综卦：序列反转
        int[] r = new int[9];
        for (int i = 0; i < 9; i++) r[i] = g[8 - i];
        return r;
    }
    public static int[] fh(int[] g) {          // 互卦：内核投影，输出5维 [g3,g4,g5,g6,g7]
        return new int[]{g[2], g[3], g[4], g[5], g[6]};
    }
    public static int[] fb(int[] g, int pos) { // 变爻：pos 0..8；F_B(+1)=0,F_B(-1)=0,F_B(0)=+1
        int[] r = g.clone();
        int v = r[pos];
        r[pos] = (v == 0) ? 1 : 0;
        return r;
    }
    public static int[] fcz(int[] g) {         // 错综复合：先综后错
        return fc(fz(g));
    }

    // ---------------- 距离与象义 ----------------
    public static double dist(int[] a, int[] b) {
        double s = 0;
        for (int i = 0; i < 9; i++) s += (a[i] - b[i]) * (a[i] - b[i]);
        return Math.sqrt(s);
    }

    // 解读坐标系：9 爻位 × 三态 → 诗评判定短语（从卦确定性映射，作为解读的出处基座）
    private static final String[][] COORD = {
        {"主旨显豁", "主旨中和", "诗旨深隐"},       // 1 显/衡/隐
        {"情感浓烈", "情感温润", "情感含蓄"},       // 2
        {"意象具象", "意象虚实相生", "意象虚淡"},   // 3
        {"白描无典", "用典适中", "用典深重"},       // 4
        {"音律谐畅", "音律中和", "音律拗涩"},       // 5
        {"修辞张力外显", "修辞平实", "修辞舒缓"},   // 6
        {"意脉贯通", "意脉从容", "意脉滞碍"},       // 7
        {"境界朗照", "境界中正", "境界幽晦"},       // 8
        {"立意根深", "立意中正", "立意浮薄"},       // 9
    };

    /** 从卦确定性输出 9 维解读坐标（可复现；与 trigram/interpret.py 的 coordinate 一致）。 */
    public static String coordinate(int[] g) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 9; i++) {
            sb.append(AXIS[i]).append("·").append(COORD[i][g[i] + 1]); // -1->0, 0->1, 1->2
            if (i < 8) sb.append("，");
        }
        return sb.toString();
    }

    /** 把卦转成象辞（映射层创作，不触碰公理）。 */
    public static String oracle(int[] g) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 9; i++) {
            sb.append(AXIS[i]).append("·");
            if (g[i] == 0) sb.append("中和持衡");
            else sb.append(IMG[i][g[i] == 1 ? 0 : 1]);
            if (i < 8) sb.append("，");
        }
        return sb.toString();
    }

    // ---------------- 语料与检索 ----------------
    public static class Poem {
        public String title, author, text, topic, interpretation;
        public int age;
        public int[] gua;
    }

    /** 从 JSON 加载语料。 */
    public static List<Poem> load(JSONArray arr) {
        List<Poem> list = new ArrayList<>();
        for (int i = 0; i < arr.length(); i++) {
            JSONObject o = arr.optJSONObject(i);
            Poem p = new Poem();
            p.title = o.optString("title");
            p.author = o.optString("author");
            p.text = o.optString("text");
            p.topic = o.optString("topic");
            p.interpretation = o.optString("interpretation");
            p.age = o.optInt("age");
            JSONArray ga = o.optJSONArray("gua");
            p.gua = new int[9];
            for (int j = 0; j < 9; j++) p.gua[j] = ga.optInt(j);
            list.add(p);
        }
        return list;
    }

    /** 按年龄段分类：目标卦=年龄段风格卦，在本年龄段语料内按欧氏距离排序取 Top-N。 */
    public static List<Poem> classify(List<Poem> all, int ageIdx, int topN) {
        int[] target = AGE_GUA[ageIdx];
        List<Poem> bucket = new ArrayList<>();
        for (Poem p : all) if (p.age == ageIdx) bucket.add(p);
        Collections.sort(bucket, (a, b) -> Double.compare(dist(target, a.gua), dist(target, b.gua)));
        return bucket.subList(0, Math.min(topN, bucket.size()));
    }

    /** 三元推演：对年龄段风格卦做变爻/错/综/互，生成衍生目标卦，从全语料检索 Top-N。 */
    public static List<int[]> deriveTargets(int ageIdx, int moveCount) {
        List<int[]> targets = new ArrayList<>();
        int[] base = AGE_GUA[ageIdx];
        targets.add(base);
        targets.add(fc(base));
        targets.add(fz(base));
        targets.add(fcz(base));
        // 变爻：对前 moveCount 爻位各动一次
        for (int i = 0; i < Math.min(moveCount, 9); i++) targets.add(fb(base, i));
        return targets;
    }

    // ---------------- 三元原创（创作诗） ----------------
    public static class OrigPoem {
        public String op, title, text, oracle, interpretation;
        public int age;
        public int[] gua;
    }

    public static List<OrigPoem> loadOrig(JSONArray arr) {
        List<OrigPoem> list = new ArrayList<>();
        for (int i = 0; i < arr.length(); i++) {
            JSONObject o = arr.optJSONObject(i);
            OrigPoem p = new OrigPoem();
            p.op = o.optString("op");
            p.title = o.optString("title");
            p.text = o.optString("text");
            p.oracle = o.optString("oracle");
            p.interpretation = o.optString("interpretation");
            p.age = o.optInt("age");
            JSONArray ga = o.optJSONArray("gua");
            p.gua = new int[9];
            for (int j = 0; j < 9; j++) p.gua[j] = ga.optInt(j);
            list.add(p);
        }
        return list;
    }

    /** 取某年龄段的 4 首三元原创（原数据顺序：本卦/错卦/动中爻/动境界爻）。 */
    public static List<OrigPoem> origByAge(List<OrigPoem> all, int ageIdx) {
        List<OrigPoem> out = new ArrayList<>();
        for (OrigPoem p : all) if (p.age == ageIdx) out.add(p);
        return out;
    }

    // ---------------- 深度卦典（内嵌精简版） ----------------
    private static JSONObject QUANJI = null;

    /** 加载 assets/sanjiu_quanji_apk.json（本 App 诗词命中的卦典，完整 19683 见开源仓库）。 */
    public static void initQuanji(Context ctx) {
        if (QUANJI != null) return;
        try {
            InputStream is = ctx.getAssets().open("sanjiu_quanji_apk.json");
            java.io.ByteArrayOutputStream b = new java.io.ByteArrayOutputStream();
            byte[] buf = new byte[8192];
            int n;
            while ((n = is.read(buf)) != -1) b.write(buf, 0, n);
            is.close();
            QUANJI = new JSONObject(new String(b.toByteArray(), "UTF-8"));
        } catch (Exception e) {
            QUANJI = null;
        }
    }

    /** 9 维向量 → 19683 卦唯一索引 0..19682（三进制，与 trigram 一致）。 */
    public static int idxOf(int[] g) {
        int n = 0;
        for (int v : g) n = n * 3 + (v + 1);
        return n;
    }

    /** 按卦典索引取深度卦辞全文（卦名 + 总释/分层/制衡/自适配/演化）；未内嵌返回 null。 */
    public static String getQuanji(int idx) {
        if (QUANJI == null) return null;
        try {
            JSONObject g = QUANJI.getJSONObject(String.valueOf(idx));
            StringBuilder sb = new StringBuilder();
            sb.append("卦名：").append(g.optString("name")).append("\n");
            sb.append("上").append(g.optString("U")).append("·中").append(g.optString("M"))
              .append("·下").append(g.optString("B")).append("\n\n");
            sb.append("【复合卦总释】\n").append(g.optString("zongshi")).append("\n\n");
            sb.append("【分层拆解】\n").append(g.optString("fenceng")).append("\n\n");
            sb.append("【跨层制衡】\n").append(g.optString("zhiheng")).append("\n\n");
            sb.append("【全局自适配能力评估】\n").append(g.optString("zishiying")).append("\n\n");
            sb.append("【演化路径】\n").append(g.optString("yanhua"));
            return sb.toString();
        } catch (Exception e) {
            return null;
        }
    }

    /** 取卦名（供卡片标题）。 */
    public static String quanjiName(int idx) {
        if (QUANJI == null) return "";
        try {
            return QUANJI.getJSONObject(String.valueOf(idx)).optString("name");
        } catch (Exception e) {
            return "";
        }
    }
}
