from pydantic import BaseModel, Field


# class MDPVDataDoc(BaseModel):

#     task_label: str = Field(None, description="The name of the task.")
#     volume: float = Field(None, description="The volume data from the MD run")
#     pressure: float = Field(None, description="The volume data from the MD run")
class MDPVDataDoc(BaseModel):
    task_label: str = Field(None, description="The name of the task.")
    volume: float = Field(None, description="The volume data from the MD run")
    pressure: float = Field(None, description="The volume data from the MD run")    
    # other fields...

    @property
    def task_label(self):
        return self.__dict__['task_label']

    @task_label.setter
    def task_label(self, value):
        if value is None:
            raise ValueError("task_label should not be None")
        self.__dict__['task_label'] = value