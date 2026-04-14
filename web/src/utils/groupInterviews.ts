import type { Interview, InterviewGroup, Job } from '@/types';

const STATUS_PRIORITY: Record<number, number> = {
  1: 0, // 进行中 — 最高
  2: 1, // 已完成
  0: 2, // 待开始
  3: 3, // 已中断
  4: 4, // 已过期 — 最低
};

function getPriority(status: number): number {
  return STATUS_PRIORITY[status] ?? 99;
}

export function groupInterviewsByJob(
  interviews: Interview[],
  jobs: Job[],
): InterviewGroup[] {
  const jobNameMap = new Map<number, string>();
  for (const j of jobs) jobNameMap.set(j.id, j.name);

  // 按 job_id 分桶
  const buckets = new Map<number, Interview[]>();
  for (const iv of interviews) {
    let list = buckets.get(iv.job_id);
    if (!list) {
      list = [];
      buckets.set(iv.job_id, list);
    }
    list.push(iv);
  }

  const groups: InterviewGroup[] = [];
  for (const [jobId, list] of buckets) {
    // API 返回按 id desc，list 已是时间倒序
    // 选代表：优先级最高（数值最小），同优先级取 id 最大
    const representative = list.reduce((best, cur) => {
      const bp = getPriority(best.status);
      const cp = getPriority(cur.status);
      if (cp < bp) return cur;
      if (cp === bp && cur.id > best.id) return cur;
      return best;
    });

    groups.push({
      job_id: jobId,
      job_name: jobNameMap.get(jobId) ?? `岗位 #${jobId}`,
      representative,
      history: list,
    });
  }

  // 排序：按代表记录优先级，同级按代表时间倒序
  groups.sort((a, b) => {
    const pa = getPriority(a.representative.status);
    const pb = getPriority(b.representative.status);
    if (pa !== pb) return pa - pb;
    return b.representative.id - a.representative.id;
  });

  return groups;
}
