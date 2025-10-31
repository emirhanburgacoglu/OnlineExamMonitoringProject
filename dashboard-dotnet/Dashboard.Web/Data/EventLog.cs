// Data/EventLog.cs (Güncellenmiş Hali)
using System.ComponentModel.DataAnnotations;

namespace Dashboard.Web.Data
{
    public class EventLog
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public string EventType { get; set; } = string.Empty;
        [Required]
        public double SuspicionScore { get; set; }
        [Required]
        public DateTime Timestamp { get; set; }

        // --- YENİ EKLENEN İLİŞKİLER (Foreign Keys) ---
        
        // Bu olayın hangi öğrenciye ait olduğunu belirtir
        public int StudentId { get; set; }
        public Student Student { get; set; } = null!;

        // Bu olayın hangi sınava ait olduğunu belirtir
        public int ExamId { get; set; }
        public Exam Exam { get; set; } = null!;
    }
}