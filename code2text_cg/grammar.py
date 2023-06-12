from code2text.translate import Pattern
from tree_sitter_apertium import CG

base_rules = [
    {'pattern': '[(semicolon) (comment)] @root', 'output': ''},
    {
        'pattern': '(source_file (_) @thing_list) @root',
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
    [(contexttest) @test_list "(" ")"]*
  ) @root
  (#match? @type "^SELECT$")
)
''',
        'output': [
            {
                'cond': [
                    {'has': 'test_list'}
                ],
                'output': 'If {test_list}, keep only readings matching {target}.',
                'lists': {
                    'test_list': {
                        'join': ' and '
                    }
                }
            },
            {
                'output': 'Keep only readings matching {target}'
            }
        ]
    },
    {
        'pattern': '''
(
  (rule
    (ruletype) @type
    (rule_target (_) @target)
    [(contexttest) @test_list "(" ")"]*
  ) @root
  (#match? @type "^REMOVE$")
)
''',
        'output': [
            {
                'cond': [
                    {'has': 'test_list'}
                ],
                'output': 'If {test_list}, remove any readings matching {target}.',
                'lists': {
                    'test_list': {
                        'join': ' and '
                    }
                }
            },
            {
                'output': 'Keep only readings matching {target}'
            }
        ]
    },
    {
        'pattern': '(section_header) @root',
        'output': 'Start a new section.',
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
  (#match? @name "^DELIMITERS$")
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
        'pattern': '(taglist (tag)+ @tag_list) @root',
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
        'pattern': '(compotag "(" (tag)+ @tag_list ")") @root',
        'output': [{
            'lists': {'tag_list': {'join': ' and '}},
            'output': '({tag_list})',
        }],
    },
    {
        'pattern': '(list (setname) @name_text (taglist [(tag) (compotag)]+ @tag_list)) @root',
        'output': [{
            'lists': {'tag_list': {'join': ' or '}},
            'output': 'Define the set {name_text} as matching {tag_list}.',
        }],
    },
    {
        'pattern': '(contexttest (contextpos) @ctx_text (inlineset (_) @set) (LINK) (contexttest) @link) @root',
        'output': 'the word at position {ctx_text} matches {set} and, relative to that, {link}',
    },
    {
        'pattern': '(contexttest (contextpos) @ctx_text (inlineset (_) @set) !link) @root',
        'output': 'the word at position {ctx_text} matches {set}',
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
]

rules = [Pattern.from_json(CG, rl) for rl in base_rules]
