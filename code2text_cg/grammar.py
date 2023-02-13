from code2text.translate import Pattern
from tree_sitter_apertium import CG

base_rules = [
    {'pattern': '(semicolon) @root', 'output': ''},
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
    {
        'pattern': '(contexttest (contextpos) @pos_text (_) @set) @root',
        'output': 'the cohort at position {pos_text} matches {set}'
    },
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
]

rules = [Pattern.from_json(CG, rl) for rl in base_rules]
