from code2text.translate import Pattern
from tree_sitter_apertium import CG

def multi_option(*args, lists=None, cap=True):
    from itertools import product
    ops = []
    for cond, out in args:
        if isinstance(cond, str):
            ls = cond
            if not isinstance(cond, list):
                ls = [ls]
            ops.append([
                ([{'has': c} for c in ls], out),
                ([], ''),
            ])
        elif isinstance(cond, tuple) and cond[1] == False:
            ls = cond[0]
            if not isinstance(ls, list):
                ls = [ls]
            ops.append([
                ([{'has': c} for c in ls], ''),
                ([], out),
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

def set_op_set(pred, pat):
    return {
        'pattern': '''
        (inlineset
          (set_op) @op
          .
          (inlineset_single (setname) @name) @root
          %s
        )
        ''' % pred,
        'output': pat,
    }
def set_op_tag(pred, pat):
    return {
        'pattern': '''
        (inlineset
          (set_op) @op
          .
          (inlineset_single (taglist) @tags) @root
          %s
        )
        ''' % pred,
        'output': pat,
    }

base_rules = [
    {'pattern': '[(semicolon) (comment)] @root', 'output': ''},
    {
        'pattern': '(source_file (_)* @thing_list) @root',
        'output': [
            {
                'lists': {
                    'thing_list': {
                        'join': '\n',
                        'html_type': 'p',
                    }
                },
                'output': '{thing_list}'
            }
        ]
    },
    {
        'pattern': '(rule ["(" ")"] @root)',
        'output': ''
    },
    ########################################
    ## Declarations
    ########################################
    {
        'pattern': '(section_header) @root',
        'output': 'Start a new section.',
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
        'pattern': '(list (setname) @name_text (taglist [(tag) (compotag)]* @tag_list)) @root',
        'output': [{
            'lists': {'tag_list': {'join': ' or '}},
            'output': 'Define the set {name_text} as matching {tag_list}.',
        }],
    },
    {
        'pattern': '''(set
          name: (setname) @name_text
          value: (inlineset) @value
        ) @root''',
        'output': 'Define the set {name_text} as any word {value}.',
    },
    ########################################
    ## Rules
    ########################################
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
            ('test_list', 'if {test_list} then '),
            (None, 'delete any reading unless it is one {target}.'),
            lists={'test_list': {'join': ' and ', 'html_type': 'ul'}},
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
            ('test_list', 'if {test_list} then '),
            (None, 'remove any reading {target}.'),
            lists={'test_list': {'join': ' and ', 'html_type': 'ul'}},
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
            ('test_list', 'if {test_list} then '),
            (None, 'remove tags and restrictions added by MAP for a word {target}.'),
            lists={'test_list': {'join': ' and ', 'html_type': 'ul'}},
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
            ('test_list', 'if {test_list} then '),
            (None, 'delete any word {target}.'),
            lists={'test_list': {'join': ' and ', 'html_type': 'ul'}},
        ),
    },
    {
        'pattern': '''
        (
          (rule_substitute_etc
            (ruletype_substitute_etc) @type
            (inlineset (inlineset_single [(taglist) (setname)] @src))
            (inlineset (inlineset_single [(taglist) (setname)] @trg))
            (rule_target (_) @target)
            [(contexttest)* @test_list "(" ")"]*
          ) @root
          (#eq? @type "SUBSTITUTE")
        )
        ''',
        'output': multi_option(
            ('test_list', 'if {test_list} then '),
            (None, 'replace {src} with {trg} in any reading {target}.'),
            lists={'test_list': {'join': ' and ', 'html_type': 'ul'}},
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
            ('test_list', 'if {test_list} then '),
            (None, 'set the parent of any word {target} to {ctxtarget}.'),
            lists={'test_list': {'join': ' and ', 'html_type': 'ul'}},
        ),
    },
    {
        'pattern': '''
        (
          (rule_parentchild
            type: (ruletype_parentchild) @type
            trg: (_) @target
            context: (contexttest)* @test_list
            (contexttest) @ctxtarget
            (contexttest)* @ctx_list
          ) @root
          (#eq? @type "SETCHILD")
        )
        ''',
        'output': multi_option(
            ('test_list', 'if {test_list} then '),
            (None, 'set a word {target} as the parent of a word {ctxtarget}.'),
            lists={'test_list': {'join': ' and ', 'html_type': 'ul'}},
        ),
    },
    {
        'pattern': '''
        (
          (rule_map_etc
            type: (ruletype_map_etc) @type
            tags: (inlineset (inlineset_single [(taglist) (setname)] @tags))
            target: (rule_target (_) @target)
            context: [(contexttest) @test_list "(" ")"]*
          ) @root
          (#eq? @type "MAP")
        )
        ''',
        'output': multi_option(
            ('test_list', 'if {test_list} then '),
            (None, 'add {tags} to a word {target} and prevent other rules from adding tags.'),
            lists={'test_list': {'join': ' and ', 'html_type': 'ul'}},
        ),
    },
    {
        'pattern': '''
        (
          (rule_map_etc
            type: (ruletype_map_etc) @type
            tags: (inlineset (inlineset_single [(taglist) (setname)] @tags))
            target: (rule_target (_) @target)
            context: (contexttest)* @test_list
          ) @root
          (#eq? @type "ADD")
        )
        ''',
        'output': multi_option(
            ('test_list', 'if {test_list} then '),
            (None, 'add {tags} to a word {target}.'),
            lists={'test_list': {'join': ' and ', 'html_type': 'ul'}},
        ),
    },
    {
        'pattern': '''
        (
          (rule_with
            trg: (rule_target (_) @target)
            context: [(contexttest) @test_list "(" ")"]*
            children: (_)* @rule_list
          ) @root
        )
        ''',
        'output': multi_option(
            (None, 'find a word {target}'),
            ('test_list', ' in context {test_list}'),
            (None, ' and run the following rules:\n  {rule_list}'),
            lists={
                'test_list': {'join': ' and ', 'html_type': 'ol'},
                'rule_list': {'join': '\n  ', 'html_type': 'ol'},
            },
        ),
    },
    ########################################
    ## Contextual Tests
    ########################################
    {
        'pattern': '''
        (contexttest
          modifier: [
            (context_modifier) @all
            (context_modifier) @none
            (context_modifier) @not
            (context_modifier) @negate
          ]*
          (#eq? @all "ALL")
          (#eq? @none "NONE")
          (#eq? @not "NOT")
          (#eq? @negate "NEGATE")
          (contextpos) @ctx
          set: (_) @set
          barrier: (inlineset)? @barrier
          link: (contexttest)? @link
        ) @root
        ''',
        'output': multi_option(
            ('negate', 'it is not the case that '),
            ('all', 'every '),
            ('none', 'no '),
            ((['all', 'none'], False), 'some '),
            (None, '{ctx} '),
            ('barrier', '(stop looking if you reach one {barrier}) '),
            (None, 'is '),
            ('not', 'not '),
            (None, 'one {set}'),
            ('link', ' and, relative to that, {link}'),
            cap=False,
        ),
    },
    {
        'pattern': '(contextpos . (ctx_parent) .) @root',
        'output': 'parent',
    },
    {
        'pattern': '(contextpos . (ctx_sibling) .) @root',
        'output': 'sibling',
    },
    {
        'pattern': '(contextpos . (ctx_child) .) @root',
        'output': 'child',
    },
    {
        'pattern': '(contextpos) @root_text',
        'output': 'word at position {root_text}',
    },
    ########################################
    ## Set Operators
    ########################################
    {
        'pattern': '(inlineset [(inlineset_single) @child_list (set_op)]*) @root',
        'output': [{
            'lists': {'child_list': {'join': ' '}},
            'output': '{child_list}',
        }],
    },
    {
        'pattern': '(inlineset . (inlineset_single (setname) @name) @root)',
        'output': 'which matches {name}',
    },
    {
        'pattern': '(inlineset . (inlineset_single (taglist) @tags) @root)',
        'output': 'which has {tags}',
    },
    set_op_set('(#match? @op "^([oO][rR]|[|])$")', 'or matches {name}'),
    set_op_tag('(#match? @op "^([oO][rR]|[|])$")', 'or has {tags}'),
    set_op_set('(#eq? @op "+")', 'and matches {name}'),
    set_op_tag('(#eq? @op "+")', 'and has {tags}'),
    set_op_set('(#eq? @op "-")', 'and does not match {name}'),
    set_op_tag('(#eq? @op "-")', 'and does not have {tags}'),
    ########################################
    ## Sets and Tags
    ########################################
    {
        'pattern': '''
        (rule_with (_ (rule_target
          (inlineset . (inlineset_single (taglist . (tag) @t .)) .)
          (#eq? @t "*")
        ) @root))
        ''',
        'output': 'the target of the containing WITH rule',
    },
    {
        'pattern': '''(rule_target
          (inlineset . (inlineset_single (setname) @name_text) .)
        ) @root''',
        'output': 'a reading matching the set {name_text}',
    },
    {
        'pattern': '''(rule_target
          (inlineset) @desc
        ) @root''',
        'output': 'a reading matching {desc}',
    },
    {
        'pattern': '''(inlineset
          (inlineset_single . (taglist (tag) @t (#eq? @t "*")) .)
        ) @root''',
        'output': 'any word',
    },
    *[
        {
            'pattern': '''(inlineset . (inlineset_single
              (setname) @name
              (#eq? @name "_C%d_")
            ) .) @root
            ''' % i,
            'output': 'context item %d of the containing WITH rule' % i
        }
        for i in range(1, 10)
    ],
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
        'pattern': '''(taglist . (tag) @tg .) @root''',
        'output': 'the tag {tg}',
    },
    {
        'pattern': '''(inlineset
          . (inlineset_single . (taglist (tag)+ @t_list) .) .) @root''',
        'output': [{
            'lists': {'t_list': {'join': ', '}},
            'output': 'the tags {t_list}',
        }],
    },
    {
        'pattern': '(compotag "(" (tag)* @tag_list ")") @root',
        'output': [{
            'lists': {'tag_list': {'join': ' and '}},
            'output': '({tag_list})',
        }],
    },
    {
        'pattern': '(taglist (tag)* @tag_list) @root',
        'output': [{
            'lists': {'tag_list': {'join': ', '}},
            'output': 'tags {tag_list}',
        }],
    },
    {
        'pattern': '''
(
  (inlineset_single (setname) @name_text) @root
  (#match? @name_text "^[$][$].*$")
)''',
        'output': 'the set {name_text}, which must be the same as other instances of {name_text} in this rule',
    },
    {
        'pattern': '(setname) @root_text',
        'output': 'the set {root_text}',
    },
]

rules = [Pattern.from_json(CG, rl) for rl in base_rules]
