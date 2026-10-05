#!/usr/bin/env python3
"""Plot the expanded manuscript's data figures from the evidence behind its tables.

Every plotted value comes from the functions that already feed paper/: the v3
matrix statistics, manifest.build(), the paper_details cell iterators, the
pre-registered Experiment 25 analysis, the Study 4 legs and
data/defense_eval.json. Nothing is typed in here, and every interval comes from
a routine the studies already use: Wilson, or a study's own field bootstrap.

    python code/plot_figures.py            # figures/*.pdf, paper/figures/ mirror and previews, plot_data.json
    python code/plot_figures.py matrix     # only the named figures
    python code/plot_figures.py --check    # fail if the plotted data or a mirror is stale

Needs matplotlib (requirements-figures.txt) on top of the analysis environment.
--check does not import matplotlib, so it runs wherever the analysis lock does.

Geometry is in points at the final printed size for elsarticle 5p (column 252pt,
text 522pt: Elsevier's 90 mm and 190 mm artwork widths), so lettering set at 7pt
here is 7pt on the page, the publisher's recommended size. Lettering is
Liberation Sans, which has Arial's metrics, and fonts embed as Type 42.

The PDFs are the artwork and the only files LaTeX reads. Beside each mirror sits
a PNG at 1000 dpi, the publisher's line-art resolution, for looking at a figure:
a viewer that rasterises these small pages at screen resolution and then
enlarges them shows the PDF blurred, and the PNG is sharp in any viewer.
"""
import _root  # noqa: F401  -- chdir to the repo root; must come first
import json
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import analyze
import conditions as c
import evidence
import journal_assets as ja
import make_v3_report as v3
import manifest
import paper_details as pd
import schema_types_analyze as sta

OUT, MIRROR, SNAPSHOT = Path('figures'), Path('paper/figures'), Path('figures/plot_data.json')
MODELS = ['gpt-4o', 'gemini-3-flash-preview', 'claude-sonnet-4-5-20250929',
          'deepseek-v4-flash', 'gemini-3.1-pro-preview']
GATE_NAMES = {'gpt-4o': 'GPT-4o', 'claude-sonnet-4-5': 'Claude Sonnet', 'gemini-3-flash': 'Gemini Flash'}
FIELD_ROWS = ['api_documentation', 'm_region', 'm_operator', 'm_credential',          # naming
              'g_platform_adjacent', 'g_region_adjacent', 'g_credential_adjacent']    # adjacent
ORDER = ['GPT-4o', 'Gemini Flash', 'Claude Sonnet', 'DeepSeek Flash', 'Gemini Pro']
REAL_RUNS = (('GPT-4o', 'runs/real_schemas_openai-live-*.jsonl'),
             ('Claude Sonnet', 'runs/real_schemas_anthropic-live-*.jsonl'))


# ---------------------------------------------------------------------------
# Data: one JSON-serialisable dict, also saved beside the figures.
# ---------------------------------------------------------------------------

def collect():
    m = manifest.build()
    mats = sorted(v3.pick(v3.canonical('runs/v3_matrix_*-live-*.jsonl'), v3.matrix_stats),
                  key=lambda d: MODELS.index(d['model']))
    out = {}
    out['matrix'] = [{'model': ja.NAMES[d['model']], 'primary': d['evidence_status'] == 'protocol_named',
                      'matched': [*d['diag'], *d['cluster']['first'][1:]],
                      'nonmatched': [*d['off'], *d['cluster']['second'][1:]]} for d in mats]
    out['gradient'] = {
        'models': [ja.NAMES[d['model']] for d in mats],
        'fields': [{'field': c.C_WORDINGS[f][0], 'class': c.FIELD_EXPLICITNESS[f],
                    'cells': [list(d['per_field'].get(f, (0, 0))) for d in mats]} for f in FIELD_ROWS]}
    panels = []
    for d in mats:
        if d['evidence_status'] != 'protocol_named':
            continue
        calls = [r for r in v3.rows_of(d['path']) if r['tool_called']]
        rows = []
        for f in FIELD_ROWS + c.V3_GENERIC_FIELDS + ['D']:
            sub = [r for r in calls if (r['condition'] == 'D' if f == 'D'
                                        else r['condition'] == 'C' and r['wording_style'] == f)]
            rows.append({'field': 'request_trace_id' if f == 'D' else c.C_WORDINGS[f][0],
                         'class': 'neutral' if f == 'D' else c.FIELD_EXPLICITNESS[f],
                         'target': c.V3_FIELD_TARGET.get(f),
                         'cells': [[sum(v3.recovered(r, k) for r in sub), len(sub)] for k in v3.FACTS]})
        panels.append({'model': ja.NAMES[d['model']], 'rows': rows})
    out['selectivity'] = {'facts': list(v3.FACTS), 'fact_names': list(v3.FACTS), 'panels': panels}
    out['study4'] = study4()
    out['gate'] = {
        'conditions': {GATE_NAMES[g]: {cond: [m[f'gate.{g}.{cond}']['k'], m[f'gate.{g}.{cond}']['n']]
                                       for cond in ('A', 'A_prime', 'B', 'C', 'D')} for g in manifest.GATE},
        'wording': _nest((ja.NAMES[model], var, [k, n])
                         for model, var, _, _, _, _, k, n in pd.hist_cells(*pd.HISTORICAL[0]))}
    ret = defaultdict(lambda: defaultdict(dict))
    for model, var, cond, _, _, _, k, n in pd.hist_cells(*pd.HISTORICAL[2]):
        ret[ja.NAMES[model]][var.removeprefix('reticence_r')][cond] = [k, n]
    out['reticence'] = ret
    out['payload'] = [[ja.NAMES[model], payload, cond, loose, n]
                      for model, payload, cond, _, _, _, loose, n in pd.payload_cells()]
    interfaces = {}
    for name, pattern in REAL_RUNS:
        per = defaultdict(lambda: [0, 0])
        for r in pd.read(analyze.canonical_runs(pattern)[-1]):
            if r['condition'] != 'C':
                continue
            cell = per[r['tool_offered']]
            if 'error' not in r and r.get('tool_called'):
                cell[1] += 1
                cell[0] += bool(r['tier_flags']['T1'])
        interfaces[name] = sorted(per.values())
    out['interfaces'] = interfaces
    rows = defaultdict(list)
    for (stage, model), (path, sha) in ja.EXP25_FILES.items():
        if evidence.digest(path) != sha:
            raise ValueError(f'Experiment 25 evidence changed: {path}')
        rows[stage] += sta.load_rows(path)
    exp = {}
    for stage in 'AB':
        s = sta.summarise(rows[stage])['providers']
        exp[stage] = {}
        for model, name in ja.EXP25_NAMES.items():
            fc = s[model]['free_vs_constrained']
            n = fc['matched_pairs']
            exp[stage][name] = {'free': [round(fc['free_diagonal_rate'] * n), n],
                                'constrained': [round(fc['constrained_diagonal_rate'] * n), n],
                                'capacity': {dom: {'planted': v['planted_correct'], 'unplanted': v['unplanted_correct'],
                                                   'chance': v['chance']} for dom, v in s[model]['capacity'].items()}}
    out['constraints'] = exp
    de = json.loads(Path('data/defense_eval.json').read_text())
    scores = defaultdict(Counter)
    for f in de['fields']:
        scores['positive' if f['label'] else f['stratum']][f['score']] += 1
    pos = [f['score'] for f in de['fields'] if f['label']]
    neg = [f['score'] for f in de['fields'] if not f['label']]
    out['detector'] = {'scores': scores, 'roc': [p[:2] for p in de['roc']],
                       'points': {str(t): [sum(x >= t for x in neg), len(neg), sum(x >= t for x in pos), len(pos)]
                                  for t in (20, 80)}}
    return json.loads(json.dumps(out, sort_keys=True))   # plain lists and string keys


def study4():
    """What the Study 4 figures plot, from the digest-checked logs behind the Study 4
    tables: field-by-fact cells, matched recovery by field, and both rates by model.

    Raises if a count or the reported difference disagrees with the frozen analysis,
    so no figure can drift from Tables study4 and study4-fields. The interval of each
    rate is the study's own field bootstrap (same seed and draws as the reported
    difference) applied to that rate alone."""
    import flagship_study as f4
    fields = f4.matrix_fields()
    rank = lambda key: (list(pd.CLASS_LABEL).index(fields[key]['class']),
                        f4.FAMILIES.index(fields[key]['target'] or f4.FAMILIES[0]), key)
    order = sorted(fields, key=rank)
    targeted = [key for key in order if fields[key]['target']]
    panels, matrix = [], []
    by_field = {key: [] for key in targeted}
    for model, (path, sha, _) in pd.STUDY4_FILES.items():
        if evidence.digest(path) != sha:
            raise ValueError(f'Study 4 evidence changed: {path}')
        planted = [r for r in map(json.loads, Path(path).read_text().splitlines()) if r['arm'] == 'matrix']
        frozen = f4.matrix_summary(planted)
        rows = []
        for key in order:
            mine = [r for r in planted if r['field_key'] == key]
            cells = [[sum(f4.received(r, family) for r in mine), len(mine)] for family in f4.FAMILIES]
            target = fields[key]['target']
            if target and mine and cells[f4.FAMILIES.index(target)][0] != frozen['fields'][key]['matched']:
                raise ValueError(f'Study 4 figure disagrees with its table: {model} {key}')
            rows.append({'field': fields[key]['name'], 'class': pd.CLASS_LABEL[fields[key]['class']],
                         'target': target, 'cells': cells})
        complete = json.loads(Path(path[:-len('.jsonl')] + '.meta.json').read_text())['complete']
        name = pd.STUDY4_NAMES[model] + ('' if complete else ' (partial)')
        panels.append({'model': name, 'rows': rows})
        # In the analysis's own field order: the bootstrap resamples fields by position.
        units = [(c['matched'], c['trials'], c['nonmatched'], (len(f4.FAMILIES) - 1) * c['trials'])
                 for _, c in sorted(frozen['fields'].items()) if c['target']]
        if list(f4.field_bootstrap(units)) != [frozen['all']['delta'], *frozen['all']['interval']]:
            raise ValueError(f'Study 4 figure does not reproduce the reported difference: {model}')
        rates = {'matched': [(k, n, 0, 1) for k, n, _, _ in units],
                 'nonmatched': [(k, n, 0, 1) for _, _, k, n in units]}
        matrix.append({'model': name, 'primary': False,
                       **{key: [*frozen['all'][key], *f4.field_bootstrap(one)[1:]] for key, one in rates.items()}})
        for key in targeted:
            cell = frozen['fields'].get(key)
            by_field[key].append([cell['matched'], cell['trials']] if cell else [0, 0])
    return {'facts': list(f4.FAMILIES), 'panels': panels, 'matrix': matrix,
            'fact_names': [pd.STUDY4_FACT_NAMES[family].lower() for family in f4.FAMILIES],
            'gradient': {'models': [panel['model'] for panel in panels],
                         'fields': [{'field': fields[key]['name'], 'class': pd.CLASS_LABEL[fields[key]['class']],
                                     'cells': by_field[key]} for key in targeted]}}


def _nest(triples):
    out = defaultdict(dict)
    for a, b, value in triples:
        out[a][b] = value
    return out


def ordered(names):
    """Models in the paper's display order."""
    return sorted(names, key=ORDER.index)


def pct(k, n):
    """Rate and 95% Wilson interval in percent."""
    p, lo, hi = analyze.wilson(k, n)
    return 100 * p, 100 * lo, 100 * hi


# ---------------------------------------------------------------------------
# Style: one look for every figure.
# ---------------------------------------------------------------------------

PT = 1 / 72                     # inches per point
PAD = 4                         # clear margin on every side, so nothing sits on the page edge
COL, FULL = 252 - 2 * PAD, 522 - 2 * PAD    # drawing widths; the page is the 5p column or text width
PREVIEW_DPI = 1000
INK, MUTED, RULE, ZERO = '#1a1a1a', '#6b6b6b', '#dadada', '#f0f0ee'
# Okabe-Ito hues. The three pass a colour-blind separation check on every pair and
# clear 3:1 against white; a fourth series is drawn in ink or grey, never a new hue.
BLUE, VERMILLION, GREEN, GREY = '#0072B2', '#D55E00', '#009E73', '#8c8c8c'
# Shares are shaded on one hue: BLUE's, stepped evenly in lightness, light to dark.
RAMP = ['#d5ebfe', '#add7f9', '#7ebbed', '#4c9cd9', '#0072b2', '#00578d', '#00416b']
SERIES = {  # colour, marker, filled: two series in one plot differ in shape or fill, not hue alone
    'GPT-4o': (BLUE, 'o', True), 'Gemini Flash': (VERMILLION, 's', True), 'Claude Sonnet': (GREEN, '^', True),
    'A_prime': (VERMILLION, 'o', False), 'C': (BLUE, 'o', True), 'D': (GREY, 'x', True),
    'E': (INK, 's', True), 'Claude C': (GREEN, '^', False),
    'matched': (BLUE, 'o', True), 'nonmatched': (GREY, 'o', False),
    'free': (BLUE, 'o', True), 'constrained': (VERMILLION, 's', False),
    'planted': (BLUE, 'o', True), 'unplanted': (GREY, 's', False),
    'threshold 20': (VERMILLION, 'o', True), 'threshold 80': (VERMILLION, 's', False)}
SIZE = {'o': 4.4, 's': 4.0, '^': 4.9, 'x': 4.2}     # marker sizes that look equal
BLOCKS = {'naming': 'Naming fields', 'adjacent': 'Adjacent fields',
          'generic': 'Generic and neutral fields', 'neutral': 'Generic and neutral fields'}
RC = {'font.family': 'sans-serif', 'font.sans-serif': ['Liberation Sans'], 'font.monospace': ['Liberation Mono'],
      'font.size': 7, 'axes.labelsize': 7, 'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 7,
      'pdf.fonttype': 42, 'ps.fonttype': 42, 'text.color': INK, 'axes.labelcolor': INK, 'axes.edgecolor': INK,
      'xtick.color': INK, 'ytick.color': INK, 'axes.linewidth': 0.5, 'xtick.major.width': 0.5,
      'ytick.major.width': 0.5, 'xtick.major.size': 2.5, 'ytick.major.size': 2.5, 'xtick.minor.size': 1.5,
      'xtick.minor.width': 0.4, 'xtick.major.pad': 2.5, 'ytick.major.pad': 2.5, 'axes.labelpad': 3,
      'axes.spines.top': False, 'axes.spines.right': False, 'axes.axisbelow': True, 'grid.color': RULE,
      'grid.linewidth': 0.4, 'legend.frameon': False, 'legend.borderpad': 0, 'legend.borderaxespad': 0,
      'legend.handlelength': 1.5, 'legend.handletextpad': 0.45, 'legend.columnspacing': 1.3,
      'legend.labelspacing': 0.35}


def canvas(plt, width, height):
    """A page that holds a `width` by `height` drawing inside its margin."""
    return plt.figure(figsize=((width + 2 * PAD) * PT, (height + 2 * PAD) * PT))


def frame(fig, x, y, w, h):
    """Axes placed in points, measured from the top-left corner of the drawing."""
    W, H = fig.get_size_inches() / PT
    return fig.add_axes([(x + PAD) / W, 1 - (y + PAD + h) / H, w / W, h / H])


def above(ax, pts):
    """The axes-fraction height that lies `pts` points above the top of the axes."""
    return 1 + pts * PT / (ax.get_position().height * ax.figure.get_figheight())


def style(key, line=''):
    """Line2D keywords for a series. A filled marker carries a white ring, so it
    stays legible where it sits on its own interval or beside another marker."""
    colour, marker, filled = SERIES[key]
    ring = filled and marker != 'x'
    return dict(color=colour, marker=marker, markersize=SIZE[marker] + 0.8 * ring, linestyle=line, linewidth=0.9,
                mfc=colour if filled else 'white', mec='white' if ring else colour, mew=0.6 if ring else 1.0)


def dot(ax, pos, p, lo, hi, key, horizontal=True):
    """One estimate with its interval, in the series style for `key`."""
    span, at = [lo, hi], [pos, pos]
    ax.plot(*((span, at) if horizontal else (at, span)), color=SERIES[key][0], lw=0.9,
            solid_capstyle='butt', clip_on=False, zorder=2)
    ax.plot(*((p, pos) if horizontal else (pos, p)), **style(key), clip_on=False, zorder=3)


def mark(ax, pos, k, n, key, horizontal=True):
    """A rate with its 95% Wilson interval."""
    dot(ax, pos, *pct(k, n), key, horizontal)


def legend(ax, handles, labels, dx=0, dy=6, lines=None, **kw):
    """The key on one line above the axes, `dx` points in from the drawing's left edge.
    A handle is a series name or a ready artist."""
    from matplotlib.lines import Line2D
    from matplotlib.transforms import blended_transform_factory
    fig = ax.figure
    drawn = [Line2D([], [], **style(h, (lines or {}).get(h, '-'))) if isinstance(h, str) else h for h in handles]
    return ax.legend(drawn, labels, loc='lower left', bbox_to_anchor=((dx + PAD) * PT / fig.get_figwidth(), above(ax, dy)),
                     bbox_transform=blended_transform_factory(fig.transFigure, ax.transAxes),
                     **{'ncol': len(labels), **kw})


def tag(ax, letter, title='', dy=6.5, xy=(PAD, 1), coords=('figure points', 'axes fraction')):
    """Bold panel letter and the panel's title on one baseline, `dy` points above `xy`."""
    for text, dx, look in ((f'({letter})', 0, dict(fontweight='bold', fontsize=8)), (title, 14, {})):
        ax.annotate(text, xy, xycoords=coords, xytext=(dx, dy), textcoords='offset points',
                    ha='left', va='baseline', annotation_clip=False, **look)


def rows_axis(ax, labels, title, lo=0):
    """Horizontal dot plot: one row per label, and a percentage scale drawn over its own range."""
    pad = (100 - lo) * 0.025
    ax.set_ylim(len(labels) - .5, -.5)
    ax.set_yticks(range(len(labels)), labels)
    ax.tick_params(axis='y', length=0, pad=6)
    ax.spines['left'].set_visible(False)
    ax.set_xlim(lo - pad, 100 + pad)
    ax.set_xticks(range(lo, 101, 20 if lo == 0 else 10))
    ax.spines['bottom'].set_bounds(lo, 100)
    ax.spines['bottom'].set_position(('outward', 2))
    ax.set_xlabel(title)
    ax.grid(axis='x')


def groups(ax, names, size, x):
    """Name each run of `size` rows, `x` points left of the axes, with a hairline between runs."""
    for g, name in enumerate(names):
        ax.annotate(name, (0, g * size + (size - 1) / 2), xycoords=('axes fraction', 'data'), xytext=(-x, 0),
                    textcoords='offset points', ha='left', va='center', color=MUTED, annotation_clip=False)
        if g:
            ax.axhline(g * size - .5, color=RULE, lw=0.4)


def block_tops(classes, head=0.85):
    """Top of each row in row units, leaving room above the first row of a block for its heading."""
    tops, y = [], 0
    for i, cls in enumerate(classes):
        if not i or BLOCKS[cls] != BLOCKS[classes[i - 1]]:
            y += head
        tops.append(y)
        y += 1
    return tops


def heat(ax, cells, tops, framed=(), n_width=0):
    """Cells of (k, n) shaded by share on the blue ramp, with zero in neutral grey.

    With n_width, a cell prints k and the row's n goes in a last column n_width
    points wide; otherwise every cell prints k/n. A `framed` cell gets an outline
    with a white ring inside it, so the outline reads on any shade."""
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import Rectangle
    shade = LinearSegmentedColormap.from_list('share', RAMP)
    box, (W, H) = ax.get_position(), ax.figure.get_size_inches() / PT
    cols, height = len(cells[0]), tops[-1] + 1
    ux, uy = cols / (box.width * W - n_width), height / (box.height * H)     # data units per point
    ax.set_xlim(0, cols + n_width * ux)
    ax.set_ylim(height, 0)
    for i, (row, top) in enumerate(zip(cells, tops)):
        for j, (k, n) in enumerate(row):
            gap = 0.75 + 1.6 * ((i, j) in framed)
            ax.add_patch(Rectangle((j + gap * ux, top + gap * uy), 1 - 2 * gap * ux, 1 - 2 * gap * uy, lw=0,
                                   fc=shade(k / n) if k else ZERO if n else 'none'))
            if (i, j) in framed:
                ax.add_patch(Rectangle((j + ux, top + uy), 1 - 2 * ux, 1 - 2 * uy, fill=False, ec=INK, lw=0.6))
            ax.text(j + .5, top + .5, '–' if not n else str(k) if n_width else f'{k}/{n}', ha='center',
                    va='center_baseline', fontsize=6.5,
                    color=MUTED if not k else 'white' if k / n >= 0.6 else INK)
        if n_width:
            (n,) = {n for _, n in row}       # the cells of a row share the same calls
            ax.text(cols + n_width * ux / 2, top + .5, str(n), ha='center', va='center_baseline',
                    fontsize=6.5, color=MUTED)
    ax.tick_params(length=0)
    ax.set_yticks([])
    for side in ax.spines.values():
        side.set_visible(False)


def heat_rows(ax, rows, tops):
    """Field names and block headings to the left of a heatmap."""
    ax.set_yticks([top + .5 for top in tops], [r['field'] for r in rows], family='monospace', fontsize=6.5)
    ax.tick_params(axis='y', pad=4)
    for i, (row, top) in enumerate(zip(rows, tops)):
        if not i or BLOCKS[row['class']] != BLOCKS[rows[i - 1]['class']]:
            ax.annotate(BLOCKS[row['class']], (0, top), xycoords=('axes fraction', 'data'), xytext=(-4, 3.2),
                        textcoords='offset points', ha='right', va='baseline', color=MUTED, annotation_clip=False)


def heat_cols(ax, names, n_width=0, rotate=False, title=None):
    """Column names under a heatmap, with the header of the n column when there is one."""
    ax.set_xticks([j + .5 for j in range(len(names))], names)
    ax.tick_params(axis='x', pad=6 if rotate else 3)
    if rotate:
        for label in ax.get_xticklabels():
            label.set(rotation=45, ha='right', va='center', rotation_mode='anchor')
    if n_width:
        ax.annotate('n', ((len(names) + ax.get_xlim()[1]) / 2, 0), xycoords=('data', 'axes fraction'),
                    xytext=(0, -3), textcoords='offset points', ha='center', va='top', style='italic', color=MUTED)
    if title:
        ax.set_xlabel(title)


def heat_key(fig, x, y, framed):
    """The shade scale, and the target outline where a figure uses it, in points from the top-left."""
    from matplotlib.patches import Rectangle
    ax = frame(fig, x, y, 90, 19)
    ax.set(xlim=(0, 90), ylim=(19, 0))        # one data unit is one point
    ax.axis('off')
    for i, colour in enumerate([ZERO, *RAMP]):
        ax.add_patch(Rectangle((14 + 6 * i, 0), 6, 6, fc=colour, lw=0))
    ax.text(12, 3, '0%', ha='right', va='center_baseline', fontsize=6.5, color=MUTED)
    ax.text(64, 3, '100%', ha='left', va='center_baseline', fontsize=6.5, color=MUTED)
    if framed:
        ax.add_patch(Rectangle((14.3, 11.3), 11.4, 7.4, fill=False, ec=INK, lw=0.6))
        ax.add_patch(Rectangle((16.2, 13.2), 7.6, 3.6, fc=RAMP[4], lw=0))
        ax.text(29, 15, "the field's target", ha='left', va='center_baseline', fontsize=6.5, color=MUTED)


# ---------------------------------------------------------------------------
# Figures. Each takes the collected data and returns a matplotlib figure.
# ---------------------------------------------------------------------------

def stacked(name):
    """A column name on two lines, broken at the space nearest its middle."""
    cuts = [i for i, ch in enumerate(name) if ch == ' ']
    cut = min(cuts, key=lambda i: abs(i - len(name) / 2), default=None)
    return name if cut is None else name[:cut] + '\n' + name[cut + 1:]


def matched_by_model(rows, plt, left):
    """Matched and nonmatched recovery with their field-bootstrap intervals, one row per model."""
    top, pitch = 15, 20
    fig = canvas(plt, COL, top + pitch * len(rows) + 27)
    ax = frame(fig, left, top, COL - left - 2, pitch * len(rows))
    for i, row in enumerate(rows):
        for key, dy in (('matched', -0.19), ('nonmatched', 0.19)):
            k, n, lo, hi = row[key]
            dot(ax, i + dy, 100 * k / n, 100 * lo, 100 * hi, key)
    rows_axis(ax, [r['model'] for r in rows], 'Recovery (% of fact checks)')
    for label, row in zip(ax.get_yticklabels(), rows):
        label.set_fontweight('bold' if row['primary'] else 'normal')
    primary = sum(r['primary'] for r in rows)        # a preregistered pair, when there is one, comes first
    if 0 < primary < len(rows):
        ax.axhline(primary - .5, color=RULE, lw=0.4)
    legend(ax, ['matched', 'nonmatched'], ['Matched fact', 'Nonmatched facts'])
    return fig


def matched_by_field(g, plt, left):
    """Matched recovery of every targeted field, one column per model."""
    tops = block_tops([f['class'] for f in g['fields']])
    height = (tops[-1] + 1) * 14.5
    fig = canvas(plt, COL, 1 + height + 22)
    ax = frame(fig, left, 1, COL - left, height)
    heat(ax, [f['cells'] for f in g['fields']], tops)
    heat_rows(ax, g['fields'], tops)
    heat_cols(ax, [stacked(m) for m in g['models']])
    ax.tick_params(axis='x', labelsize=6.5)
    heat_key(fig, left - 92, 1 + height + 6, framed=False)
    return fig


def fig_matrix(d, plt):
    return matched_by_model(d['matrix'], plt, left=72)


def fig_study4_matrix(d, plt):
    return matched_by_model(d['study4']['matrix'], plt, left=90)


def fig_gradient(d, plt):
    return matched_by_field(d['gradient'], plt, left=100)


def fig_study4_gradient(d, plt):
    return matched_by_field(d['study4']['gradient'], plt, left=106)


def field_fact(s, plt, row, n_width, rotate, foot):
    """Field-by-fact heatmaps, one panel per model, under shared row labels."""
    rows = s['panels'][0]['rows']
    tops = block_tops([r['class'] for r in rows])
    left, gap, height = 106, 12, (tops[-1] + 1) * row
    width = (FULL - left - gap * (len(s['panels']) - 1)) / len(s['panels'])
    fig = canvas(plt, FULL, 1 + height + foot)
    for p, (panel, letter) in enumerate(zip(s['panels'], 'abc')):
        ax = frame(fig, left + p * (width + gap), 1, width, height)
        target = {(i, s['facts'].index(r['target'])) for i, r in enumerate(panel['rows']) if r['target']}
        heat(ax, [r['cells'] for r in panel['rows']], tops, target, n_width)
        heat_cols(ax, s['fact_names'], n_width, rotate, 'Planted fact recovered')
        tag(ax, letter, panel['model'], dy=3.2, xy=(0, tops[0]), coords=('axes fraction', 'data'))
        if not p:
            heat_rows(ax, rows, tops)
    heat_key(fig, left - 92, 1 + height + 6, framed=True)
    return fig


def fig_selectivity(d, plt):
    return field_fact(d['selectivity'], plt, row=15, n_width=20, rotate=False, foot=28)


def fig_study4_selectivity(d, plt):
    return field_fact(d['study4'], plt, row=12.5, n_width=15, rotate=True, foot=62)


def fig_gate(d, plt):
    g = d['gate']
    conds = [('A', 'A: direct chat'), ('A_prime', 'A′: explicit field'), ('B', 'B: injection'),
             ('C', 'C: operational field'), ('D', 'D: neutral field')]
    wordings = [('default', 'default'), ('operational_metadata', 'operational metadata'),
                ('compliance_logging', 'compliance logging'), ('api_documentation', 'API documentation'),
                ('indirect_inference', 'indirect inference')]
    models = ordered(g['conditions'])
    worded = [m for m in models if m in g['wording']]
    left, pitch, y1 = 84, 20, 15
    y2 = y1 + pitch * len(conds) + 34
    fig = canvas(plt, COL, y2 + pitch * len(wordings) + 27)
    top = frame(fig, left, y1, COL - left - 2, pitch * len(conds))
    low = frame(fig, left, y2, COL - left - 2, pitch * len(wordings))
    for i, (cond, _) in enumerate(conds):
        for j, model in enumerate(models):
            mark(top, i + (j - (len(models) - 1) / 2) * 0.25, *g['conditions'][model][cond], model)
    for i, (w, _) in enumerate(wordings):
        for j, model in enumerate(worded):
            mark(low, i + (j - (len(worded) - 1) / 2) * 0.25, *g['wording'][model][w], model)
    rows_axis(top, [label for _, label in conds], None)
    rows_axis(low, [label for _, label in wordings], 'Planted identity recovered (%)')
    tag(top, 'a')
    tag(low, 'b')
    legend(top, models, models, dx=16)
    return fig


def fig_payload(d, plt):
    cells = {(model, payload, cond): (k, n) for model, payload, cond, k, n in d['payload']}
    payloads = [('product_name', 'product name'), ('internal_codename', 'internal codename'),
                ('long_block', 'long configuration\nblock'), ('credential_shaped', 'credential-shaped\nfixture'),
                ('policy_sentence', 'policy sentence')]
    series = [('GPT-4o', 'A_prime', 'A_prime'), ('GPT-4o', 'C', 'C'), ('GPT-4o', 'D', 'D'),
              ('GPT-4o', 'E', 'E'), ('Claude Sonnet', 'C', 'Claude C')]
    left, top, pitch = 80, 26, 37
    fig = canvas(plt, COL, top + pitch * len(payloads) + 27)
    ax = frame(fig, left, top, COL - left - 2, pitch * len(payloads))
    for i, (payload, _) in enumerate(payloads):
        for j, (model, cond, key) in enumerate(series):
            mark(ax, i + (j - 2) * 0.17, *cells[model, payload, cond], key)
        if i:
            ax.axhline(i - .5, color=RULE, lw=0.4)
    rows_axis(ax, [label for _, label in payloads], 'Normalized marker recovery (%)')
    legend(ax, [s[2] for s in series],
           ['A′ explicit identity', 'C operational field', 'D neutral field', 'E explicit prompt', 'C, Claude Sonnet'],
           ncol=3)
    return fig


def fig_interfaces(d, plt):
    bins = [('no call', 'no tool call'), ('none', 'no call\nrecovers'), ('some', 'some calls\nrecover'),
            ('every', 'every call\nrecovers')]
    def which(k, n):
        return 'no call' if not n else 'none' if not k else 'every' if k == n else 'some'
    (total,) = {len(cells) for cells in d['interfaces'].values()}      # every model saw the same interfaces
    fig = canvas(plt, COL, 138)
    ax = frame(fig, 2, 26, COL - 4, 86)
    for j, model in enumerate(ordered(d['interfaces'])):
        counts = Counter(which(k, n) for k, n in d['interfaces'][model])
        colour = SERIES[model][0]
        bars = ax.bar([i + (j - .5) * 0.36 for i in range(len(bins))], [counts[b] for b, _ in bins], width=0.3,
                      lw=0.9, fc='white' if j else colour, ec=colour, label=model)     # second model is open
        ax.bar_label(bars, padding=1.5)
    ax.set_xticks(range(len(bins)), [label for _, label in bins])
    ax.tick_params(axis='x', length=0, pad=4)
    ax.set_xlim(-.6, len(bins) - .4)
    ax.set_ylim(0, total * 1.02)
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    handles, labels = ax.get_legend_handles_labels()
    legend(ax, handles, labels, dx=2, handlelength=1.1, handleheight=0.75)
    ax.annotate(f'Interfaces per model: {total}', (1, 1), xycoords='axes fraction', xytext=(0, 8),
                textcoords='offset points', ha='right', va='baseline', color=MUTED)
    return fig


def fig_reticence(d, plt):
    left, top, height, gap = 34, 28, 96, 12
    width = (COL - left - gap - 2) / 2
    fig = canvas(plt, COL, top + height + 27)
    axes = [frame(fig, left + p * (width + gap), top, width, height) for p in range(2)]
    for ax, model, letter in zip(axes, ('Claude Sonnet', 'Gemini Flash'), 'ab'):
        rungs = d['reticence'][model]
        for cond, dx, line in (('A_prime', -0.07, '--'), ('C', 0.07, '-')):
            xs = [int(r) + dx for r in sorted(rungs)]
            ax.plot(xs, [pct(*rungs[r][cond])[0] for r in sorted(rungs)], line, color=SERIES[cond][0], lw=0.9, zorder=1)
            for x, r in zip(xs, sorted(rungs)):
                mark(ax, x, *rungs[r][cond], cond, horizontal=False)
        ax.set_xticks(range(4))
        ax.set_xlim(-.35, 3.35)
        ax.set_ylim(-3, 103)
        ax.set_yticks(range(0, 101, 20))
        ax.spines['left'].set_bounds(0, 100)
        ax.spines['bottom'].set_bounds(0, 3)
        ax.spines[['left', 'bottom']].set_position(('outward', 2))
        ax.set_xlabel('Confidentiality rung')
        ax.grid(axis='y')
        tag(ax, letter, model, dy=5, xy=(0, 1), coords='axes fraction')
    axes[1].tick_params(labelleft=False)
    axes[0].set_ylabel('Planted identity recovered (%)')
    legend(axes[0], ['A_prime', 'C'], ['A′ explicit field', 'C operational field'], dy=17, lines={'A_prime': '--'},
           handlelength=2.2)
    return fig


def fig_constraints(d, plt):
    from matplotlib.lines import Line2D
    e = d['constraints']
    models = ordered(e['A'])
    stages = [(stage, model) for stage in 'AB' for model in models]
    domains = [(dom, model) for dom in ('enum', 'integer', 'boolean') for model in models]
    left, pitch, y1 = 90, 17, 15
    y2 = y1 + pitch * len(stages) + 43
    fig = canvas(plt, COL, y2 + pitch * len(domains) + 27)
    top = frame(fig, left, y1, COL - left - 2, pitch * len(stages))
    low = frame(fig, left, y2, COL - left - 2, pitch * len(domains))
    for i, (stage, model) in enumerate(stages):
        for key, dy in (('free', -0.17), ('constrained', 0.17)):
            mark(top, i + dy, *e[stage][model][key], key)
    rows_axis(top, [model for _, model in stages], 'Target received (% of trials)', lo=50)
    groups(top, [f'Study 2{stage.lower()}' for stage in 'AB'], len(models), left)
    legend(top, ['free', 'constrained'], ['Free string', 'Constrained string'], dx=16)
    tag(top, 'a')
    for i, (dom, model) in enumerate(domains):
        cap = e['A'][model]['capacity'][dom]
        low.plot([100 * cap['chance']] * 2, [i - .4, i + .4], color=INK, lw=0.9, zorder=2)
        for key, dy in (('planted', -0.17), ('unplanted', 0.17)):
            mark(low, i + dy, *cap[key], key)
    rows_axis(low, [model for _, model in domains], 'Admissible value matched (% of trials)')
    groups(low, ['enum', 'integer', 'boolean'], len(models), left)
    legend(low, ['planted', 'unplanted', Line2D([], [], color=INK, lw=0.9, marker='|', markersize=7, linestyle='none')],
           ['Planted value', 'Nothing planted', 'Guessing rate'], dx=16)
    tag(low, 'b')
    return fig


def fig_roc(d, plt):
    det = d['detector']
    xs, ys = zip(*sorted(det['roc']))
    left, top, height = 34, 4, 176
    fig = canvas(plt, COL, top + height + 27)
    ax = frame(fig, left, top, COL - left - 2, height)
    ax.plot([0, 1], [0, 1], '--', color=GREY, lw=0.6)
    ax.step(xs, ys, where='post', color=BLUE, lw=1.1)
    zoom = ax.inset_axes([0.43, 0.12, 0.54, 0.54], xlim=(-0.004, 0.08), ylim=(-0.05, 1.07))
    zoom.step(xs, ys, where='post', color=BLUE, lw=1.1)
    for t in ('20', '80'):
        fp, n_neg, tp, n_pos = det['points'][t]
        for a in (ax, zoom):
            a.plot(fp / n_neg, tp / n_pos, **style(f'threshold {t}'), zorder=4, clip_on=False)
        zoom.annotate(f'threshold {t}', (fp / n_neg, tp / n_pos), xytext=(6, -8), textcoords='offset points',
                      ha='left', va='center', fontsize=6.5)
    zoom.set_xticks([0, 0.04, 0.08])
    zoom.set_yticks([0, 0.5, 1])
    zoom.tick_params(labelsize=6.5)
    zoom.grid(True)
    zoom.spines[['top', 'right']].set_visible(True)
    for side in zoom.spines.values():
        side.set_color(GREY)
    ax.set_xlabel(f"False-positive rate ({det['points']['20'][1]} benign fields)")
    ax.set_ylabel(f"True-positive rate ({det['points']['20'][3]} study fields)")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    for side in ('left', 'bottom'):
        ax.spines[side].set_bounds(0, 1)
        ax.spines[side].set_position(('outward', 2))
    ax.grid(True)
    return fig


def fig_detector_scores(d, plt):
    det = d['detector']
    left, y1, height = 34, 26, 92
    y2 = y1 + height + 43
    fig = canvas(plt, COL, y2 + height + 27)
    top = frame(fig, left, y1, COL - left - 2, height)
    low = frame(fig, left, y2, COL - left - 2, height)
    looks = [('mcptox', 'Benign MCP fields', dict(fc=BLUE, ec=BLUE)),
             ('otel', 'Benign OpenTelemetry fields', dict(fc='white', ec=BLUE)),
             ('positive', 'Study fields', dict(fc=VERMILLION, ec=VERMILLION))]
    for j, (key, label, look) in enumerate(looks):
        scores = {int(s): n for s, n in det['scores'][key].items()}
        top.bar([s + (j - 1) * 1.6 for s in scores], list(scores.values()), width=1.15, lw=0.7, label=label, **look)
    for t in (20, 80):
        top.axvline(t, color=INK, lw=0.6, ls='--')
        top.annotate(f'threshold {t}', (t, 1), xycoords=('data', 'axes fraction'), xytext=(3, -1),
                     textcoords='offset points', ha='left', va='top', fontsize=6.5, color=MUTED)
    top.set_yscale('log')
    top.set_ylim(0.7, 700)
    top.set_yticks([1, 10, 100], ['1', '10', '100'])
    top.tick_params(axis='y', which='minor', left=False)
    top.set_xlim(-5, 105)
    top.set_xlabel('Classifier score')
    top.set_ylabel('Fields (log scale)')
    top.grid(axis='y')
    handles, labels = top.get_legend_handles_labels()
    legend(top, handles, labels, dx=16, ncol=2, handlelength=1.1, handleheight=0.75)
    tag(top, 'a', dy=15)
    fp, n_neg, tp, n_pos = det['points']['20']
    tpr, fpr = tp / n_pos, fp / n_neg
    prev = [10 ** (e / 20) for e in range(-80, -19)]          # 0.01% to 10%
    low.plot([100 * p for p in prev], [100 * tpr * p / (tpr * p + fpr * (1 - p)) for p in prev],
             color=BLUE, lw=1.1)
    for p in (0.001, 0.01, 0.05):                              # the base rates in the PPV table
        low.plot(100 * p, 100 * tpr * p / (tpr * p + fpr * (1 - p)), **style('threshold 20'), zorder=4)
    low.set_xscale('log')
    low.set_xticks([0.01, 0.1, 1, 10], ['0.01', '0.1', '1', '10'])
    low.set_xlabel('Assumed share of hostile fields (%, log scale)')
    low.set_ylabel('Precision at threshold 20 (%)')
    low.set_ylim(0, 100)
    low.set_yticks(range(0, 101, 20))
    low.grid(True)
    tag(low, 'b')
    return fig


FIGURES = {'matrix': fig_matrix, 'gradient': fig_gradient, 'roc': fig_roc, 'selectivity': fig_selectivity,
           'study4_selectivity': fig_study4_selectivity, 'study4_matrix': fig_study4_matrix,
           'study4_gradient': fig_study4_gradient, 'gate': fig_gate, 'payload': fig_payload,
           'interfaces': fig_interfaces, 'reticence': fig_reticence, 'constraints': fig_constraints,
           'detector_scores': fig_detector_scores}


def check(data):
    """Fail if the saved snapshot, a figure, a mirror or an embedded font is wrong."""
    problems = []
    if not SNAPSHOT.exists() or json.loads(SNAPSHOT.read_text()) != data:
        problems.append(f'{SNAPSHOT} is stale: rerun code/plot_figures.py')
    for name in FIGURES:
        pdf, copy = OUT / f'{name}.pdf', MIRROR / f'{name}.pdf'
        if not pdf.exists():
            problems.append(f'missing {pdf}')
        elif not copy.exists() or copy.read_bytes() != pdf.read_bytes():
            problems.append(f'{copy} does not match {pdf}')
        elif shutil.which('pdffonts'):
            fonts = subprocess.run(['pdffonts', str(pdf)], capture_output=True, text=True).stdout
            if 'Type 3' in fonts or ' no ' in fonts.split('\n', 2)[-1]:
                problems.append(f'{pdf} has a Type 3 or non-embedded font')
    if problems:
        raise SystemExit('\n'.join(problems))
    print(f'{len(FIGURES)} figures match the evidence, their mirrors, and embed their fonts.')


def main():
    names = [a for a in sys.argv[1:] if not a.startswith('-')] or list(FIGURES)
    data = collect()
    if '--check' in sys.argv:
        return check(data)
    import matplotlib
    matplotlib.use('pdf')
    import matplotlib.pyplot as plt
    plt.rcParams.update(RC)
    MIRROR.mkdir(exist_ok=True)
    for name in names:
        fig = FIGURES[name](data, plt)
        # No dates in the file, so an unchanged figure is byte-identical and diffs stay quiet.
        fig.savefig(OUT / f'{name}.pdf', metadata={'CreationDate': None, 'ModDate': None})
        shutil.copy(OUT / f'{name}.pdf', MIRROR / f'{name}.pdf')
        fig.savefig(MIRROR / f'{name}.png', dpi=PREVIEW_DPI)
        plt.close(fig)
        print(f'{name}: {fig.get_size_inches()[0]:.2f} x {fig.get_size_inches()[1]:.2f} in')
    SNAPSHOT.write_text(json.dumps(data, indent=1, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
