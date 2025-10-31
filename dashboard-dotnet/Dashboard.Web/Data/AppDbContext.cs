// Data/AppDbContext.cs (Güncellenmiş Hali)
using Microsoft.EntityFrameworkCore;

namespace Dashboard.Web.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
        {
        }

        // Artık veritabanımızda 3 tablo olacağını biliyor
        public DbSet<Student> Students { get; set; }
        public DbSet<Exam> Exams { get; set; }
        public DbSet<EventLog> EventLogs { get; set; }
    }
}