class KnowledgeBase:
    def __init__(self):
        self.terms_mapping = {
            "hdfs": ["hadoop distributed file system", "хадуп файловая система", "распределенная фс"],
            "namenode": ["нейм нода", "name node", "мастер нода"],
            "datanode": ["дата нода", "data node", "рабочая нода"],
            "mapreduce": ["мапредьюс", "map reduce", "мап редьюс", "распределенные вычисления"],
            "hadoop": ["хадуп", "apache hadoop", "hadoop framework"],
            "wordcount": ["подсчет слов", "word count", "пример mapreduce"]
        }

        self.context_mapping = {
            "hdfs": {
                "process": "storage",
                "area": "distributed_fs",
                "full_name": "Hadoop Distributed File System - распределенная файловая система",
                "related_terms": ["блоки данных", "репликация", "namenode", "datanode"],
            },
            "mapreduce": {
                "process": "processing",
                "area": "distributed_computing",
                "full_name": "MapReduce - модель распределенных вычислений",
                "related_terms": ["mapper", "reducer", "wordcount", "distributed processing"],
            },
            "hadoop": {
                "process": "big_data",
                "area": "framework",
                "full_name": "Apache Hadoop - фреймворк для распределенной обработки",
                "related_terms": ["hdfs", "mapreduce", "yarn", "distributed computing"],
            }
        }
