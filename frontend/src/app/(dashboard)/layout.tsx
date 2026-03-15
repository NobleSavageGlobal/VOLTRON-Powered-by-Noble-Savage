import { MainLayout } from '@/components/layout/MainLayout';

export default function DashboardGroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <MainLayout>{children}</MainLayout>;
}
