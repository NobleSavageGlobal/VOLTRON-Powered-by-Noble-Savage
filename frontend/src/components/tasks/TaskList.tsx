'use client';

import { TaskCard } from './TaskCard';
import { Spinner } from '@/components/ui/Spinner';
import { useUpdateTask } from '@/hooks/useTasks';
import type { Task } from '@/lib/types';

interface TaskListProps {
  tasks: Task[];
  isLoading: boolean;
  emptyMessage?: string;
}

export function TaskList({ tasks, isLoading, emptyMessage = 'No tasks found' }: TaskListProps) {
  const { mutate: updateTask } = useUpdateTask();

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (tasks.length === 0) {
    return <p className="text-sm text-slate-500 py-8 text-center">{emptyMessage}</p>;
  }

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <TaskCard
          key={task.id}
          task={task}
          onStatusChange={(id, status) => updateTask({ id, data: { status } })}
        />
      ))}
    </div>
  );
}
