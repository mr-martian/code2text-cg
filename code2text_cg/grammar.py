from code2text.translate import Pattern
from tree_sitter_apertium import CG

def multi_option(*args, lists=None, cap=True):
    from itertools import product
    ops = []
    for cond, out in args:
        if cond:
            ops.append([
                ([{'has': cond}], out),
                ([], ''),
            ])
        else:
            ops.append([([], out)])
    ret = []
    for seq in product(*ops):
        cond = []
        out = ''
        for c, o in seq:
            cond += c
            out += o
        if cap and out:
            out = out[0].upper() + out[1:]
        ret.append({'cond': cond, 'output': out, 'lists': (lists or {})})
    return ret

base_rules = [
    {'pattern': '[(semicolon) (comment)] @root', 'output': ''},
    {
        'pattern': '(source_file (_)* @thing_list) @root',
        'output': [
            {
                'lists': {
                    'thing_list': {
                        'join': '\n'
                    }
                },
                'output': '{thing_list}'
            }
        ]
    },
    {
        'pattern': '(inlineset (inlineset_single (setname) @name_text)) @root',
        'output': 'the set {name_text}'
    },
    #{
    #    'pattern': '(contexttest (contextpos) @pos_text (_) @set) @root',
    #    'output': 'the cohort at position {pos_text} matches {set}'
    #},
    {
        'pattern': '(rule ["(" ")"] @root)',
        'output': ''
    },
    {
        'pattern': '''
(
  (rule
    (ruletype) @type
    (rule_target (_) @target)
    [(contexttest)* @test_list "(" ")"]*
  ) @root
  (#eq? @type "SELECT")
)
''',
        'output': multi_option(
            ('test_list', 'if {test_list}, '),
            (None, 'keep only readings matching {target}.'),
            lists={'test_list': {'join': ' and '}},
        ),
    },
    {
        'pattern': '''
(
  (rule
    (ruletype) @type
    (rule_target (_) @target)
    [(contexttest)* @test_list "(" ")"]*
  ) @root
  (#eq? @type "REMOVE")
)
''',
        'output': multi_option(
            ('test_list', 'if {test_list}, '),
            (None, 'remove any readings matching {target}.'),
            lists={'test_list': {'join': ' and '}},
        ),
    },
    {
        'pattern': '''
(
  (rule
    (ruletype) @type
    (rule_target (_) @target)
    [(contexttest)* @test_list "(" ")"]*
  ) @root
  (#eq? @type "UNMAP")
)
''',
        'output': multi_option(
            ('test_list', 'if {test_list}, '),
            (None, 'remove tags and restrictions added by MAP for words matching {target}.'),
            lists={'test_list': {'join': ' and '}},
        ),
    },
    {
        'pattern': '''
        (
          (rule
            (ruletype) @type
            (rule_target (_) @target)
            [(contexttest)* @test_list "(" ")"]*
          ) @root
          (#eq? @type "REMCOHORT")
        )
        ''',
        'output': multi_option(
            ('test_list', 'if {test_list}, '),
            (None, 'delete words matching {target}.'),
            lists={'test_list': {'join': ' and '}},
        ),
    },
    {
        'pattern': '''
        (
          (rule_substitute_etc
            (ruletype_substitute_etc) @type
            (inlineset) @src
            (inlineset) @trg
            (rule_target (_) @target)
            [(contexttest)* @test_list "(" ")"]*
          ) @root
          (#eq? @type "SUBSTITUTE")
        )
        ''',
        'output': multi_option(
            ('test_list', 'if {test_list}, '),
            (None, 'replace {src} with {trg} in readings matching {target}.'),
            lists={'test_list': {'join': ' and '}},
        ),
    },
    {
        'pattern': '''
        (
          (rule_parentchild
            type: (ruletype_parentchild) @type
            trg: (rule_target (_) @target)
            context: (contexttest)* @test_list
            (contexttest) @ctxtarget
            (contexttest)* @ctx_list
          ) @root
          (#eq? @type "SETPARENT")
        )
        ''',
        'output': multi_option(
            ('test_list', 'if {test_list}, '),
            (None, 'set the parent of words matching {target} to {ctxtarget}.'),
            lists={'test_list': {'join': ' and '}},
        ),
    },
    {
        'pattern': '''
        (
          (rule_map_etc
            type: (ruletype_map_etc) @type
            tags: (inlineset) @tags
            target: (rule_target (_) @target)
            context: (contexttest)* @test_list
          ) @root
          (#eq? @type "MAP")
        )
        ''',
        'output': multi_option(
            ('test_list', 'if {test_list}, '),
            (None, 'add {tags} to {target} and prevent other rules from adding tags.'),
            lists={'test_list': {'join': ' and '}},
        ),
    },
    {
        'pattern': '''
        (
          (rule_with
            trg: (rule_target (_) @target)
            context: (contexttest)* @test_list
            children: (_)* @rule_list
          ) @root
        )
        ''',
        'output': multi_option(
            (None, 'find a word matching {target}'),
            ('test_list', ' in context {test_list}'),
            (None, ' and run the following rules:\n  {rule_list}'),
            lists={
                'test_list': {'join': ' and '},
                'rule_list': {'join': '\n  '},
            },
        ),
    },
    {
        'pattern': '(section_header) @root',
        'output': 'Start a new section.',
    },
    {
        'pattern': '''(inlineset
          (inlineset_single . (taglist (tag) @t (#eq? @t "*")) .)
        ) @root''',
        'output': 'any word',
    },
    {
        'pattern': '''
(
  (tag (qtag) @tag_text) @root
  (#match? @tag_text "^\\"<.*>\\"$")
)''',
        'output': 'word form {tag_text}',
    },
    {
        'pattern': '(tag (qtag) @tag_text) @root',
        'output': 'lemma {tag_text}',
    },
    {
        'pattern': '(tag (ntag) @tag_text) @root',
        'output': '{tag_text}',
    },
    {
        'pattern': '''
(
  (set_special_list
    (special_list_name) @name
    (eq)
    (taglist (tag)* @delim_list)
  ) @root
  (#eq? @name "DELIMITERS")
)''',
        'output': [
            {
                'lists': {
                    'delim_list': {
                        'join': ' or ',
                    },
                },
                'output': 'Start a new sentence after reading {delim_list}.',
            },
        ],
    },
    {
        'pattern': '(taglist (tag)* @tag_list) @root',
        'output': [{
            'lists': {'tag_list': {'join': ', '}},
            'output': 'tags {tag_list}',
        }],
    },
    {
        'pattern': '(inlineset_single (taglist) @tags) @root',
        'output': '{tags}',
    },
    {
        'pattern': '(compotag "(" (tag)* @tag_list ")") @root',
        'output': [{
            'lists': {'tag_list': {'join': ' and '}},
            'output': '({tag_list})',
        }],
    },
    {
        'pattern': '(list (setname) @name_text (taglist [(tag) (compotag)]* @tag_list)) @root',
        'output': [{
            'lists': {'tag_list': {'join': ' or '}},
            'output': 'Define the set {name_text} as matching {tag_list}.',
        }],
    },
    {
        'pattern': '(contexttest (contextpos) @ctx (inlineset (_) @set) (LINK) (contexttest) @link) @root',
        'output': '{ctx} matches {set} and, relative to that, {link}',
    },
    {
        'pattern': '(contexttest (contextpos) @ctx (inlineset (_) @set) !link) @root',
        'output': '{ctx} matches {set}',
    },
    {
        'pattern': '(contextpos . (ctx_parent) .) @root',
        'output': 'the parent',
    },
    {
        'pattern': '(contextpos . (ctx_sibling) .) @root',
        'output': 'a sibling',
    },
    {
        'pattern': '(contextpos . (ctx_child) .) @root',
        'output': 'a child',
    },
    {
        'pattern': '(contextpos) @root_text',
        'output': 'the word at position {root_text}',
    },
    {
        'pattern': '''
(
  (inlineset_single (setname) @name_text) @root
  (#match? @name_text "^[$][$].*$")
)''',
        'output': 'a tag from the set {name_text}, which must be the same as other instances of {name_text} in this rule',
    },
    {
        'pattern': '(inlineset (inlineset_single) @a (set_op) @op_text (inlineset_single) @b) @root',
        'output': '{a} {op_text} {b}',
    },
    {
        'pattern': '(setname) @root_text',
        'output': '{root_text}',
    },
]

rules = [Pattern.from_json(CG, rl) for rl in base_rules]
