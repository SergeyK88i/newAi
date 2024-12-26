class KnowledgeBase:
    def __init__(self):
        self.terms_mapping = {
            'к4': ['критерий 4', 'шаг к4', 'devops к4', 'дфси к4'],
            'к5': ['критерий 5', 'шаг к5', 'devops к5', 'дфси к5'],
            'дфси': ['процесс дфси', 'dfsi', 'digital factory system integration'],
            'девопс': ['devops', 'девопс практики', 'непрерывная поставка'],
        }
        
        self.context_mapping = {
            'к4': {
                'process': 'дфси',
                'area': 'девопс',
                'full_name': 'Критерий 4 - Непрерывная поставка',
                'related_terms': ['ci/cd', 'пайплайн', 'автоматизация']
            },
            'к5': {
                'process': 'дфси',
                'area': 'девопс',
                'full_name': 'Критерий 5 - Управление конфигурациями',
                'related_terms': ['git', 'версионирование', 'конфигурации']
            }
        }
