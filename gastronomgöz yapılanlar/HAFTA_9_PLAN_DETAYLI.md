# GastronomGöz - Hafta 9 Detaylı İş Planı

**Tarih:** 20 Aralık 2025
**Süre:** 3 gün
**Amaç:** Backend'de olan tüm özellikleri mobil uygulamaya entegre etmek

---

## 📋 MEVCUT DURUM (20 Aralık 2025)

### ✅ Backend (100% Tamamlandı)
- 31 API endpoint hazır ve çalışıyor
- 5 API dosyası: auth.py, user.py, prediction.py, history.py, notification.py
- Database: 9 tablo
- AI modelleri: 3 model (ResNet50, U2NET, MiDaS)
- Test: %100 başarı

### ⚠️ Mobil Uygulama (70% Tamamlandı)

**Çalışan:**
- ✅ Authentication (Login, Register, Logout)
- ✅ Camera & Image Picker
- ✅ AI Prediction (%99.15 doğruluk)
- ✅ Prediction Result Screen
- ✅ 10 ekran UI'ı hazır
- ✅ Dil desteği (TR/EN)

**Eksik (30%):**
- ❌ Bildirimler sistemi (ekran yok!)
- ❌ Başarılar/Rozetler (ekran yok!)
- ❌ Streak takibi (gösterilmiyor!)
- ❌ History detay/edit/delete (UI var, çalışmıyor)
- ❌ Profile edit (UI var, çalışmıyor)
- ❌ Stats top foods (eksik)
- ❌ Token refresh (yok)
- ❌ Food classes listesi (yok)

---

## 🎯 YAPILACAKLAR LİSTESİ (23 API Entegrasyonu)

### GRUP 1: BİLDİRİMLER & BAŞARILAR (10 API) - KRİTİK
| # | API Endpoint | Durum | Mobil Servis | Ekran |
|---|--------------|-------|--------------|-------|
| 1 | GET /api/notifications | ❌ | notification_service.dart (YOK) | Notifications Screen (YOK) |
| 2 | GET /api/notifications/unread | ❌ | notification_service.dart (YOK) | Badge (Home) |
| 3 | POST /api/notifications/\<id\>/read | ❌ | notification_service.dart (YOK) | Notifications Screen |
| 4 | POST /api/notifications/read-all | ❌ | notification_service.dart (YOK) | Notifications Screen |
| 5 | GET /api/achievements | ❌ | notification_service.dart (YOK) | Achievements Screen (YOK) |
| 6 | GET /api/achievements/user | ❌ | notification_service.dart (YOK) | Achievements Screen (YOK) |
| 7 | GET /api/streak | ❌ | notification_service.dart (YOK) | Streak Widget (YOK) |
| 8 | GET /api/preferences/notifications | ❌ | notification_service.dart (YOK) | Notification Preferences (YOK) |
| 9 | PUT /api/preferences/notifications | ❌ | notification_service.dart (YOK) | Notification Preferences (YOK) |
| 10 | POST /api/admin/init-achievements | N/A | Gerekli değil | - |

### GRUP 2: HISTORY CRUD (3 API)
| # | API Endpoint | Durum | Mobil Servis | Ekran |
|---|--------------|-------|--------------|-------|
| 11 | GET /api/history/\<id\> | ❌ | history_service.dart (VAR) | History Detail (YOK) |
| 12 | PATCH /api/history/\<id\> | ⚠️ | updatePrediction() VAR | Edit Dialog (YOK) |
| 13 | DELETE /api/history/\<id\> | ⚠️ | deletePrediction() VAR | Delete Confirm (YOK) |

### GRUP 3: STATS (2 API)
| # | API Endpoint | Durum | Mobil Servis | Ekran |
|---|--------------|-------|--------------|-------|
| 14 | GET /api/stats/top-foods | ❌ | stats_service.dart (VAR) | Stats Screen |
| 15 | GET /api/stats/favorites | ❌ | stats_service.dart (VAR) | Stats Screen |

### GRUP 4: PROFILE (2 API)
| # | API Endpoint | Durum | Mobil Servis | Ekran |
|---|--------------|-------|--------------|-------|
| 16 | PUT /api/user/profile | ❌ | auth_service.dart | Edit Profile (VAR, çalışmıyor) |
| 17 | PUT /api/user/goals | ❌ | YOK | Goals Screen (YOK) |

### GRUP 5: DİĞER (3 API)
| # | API Endpoint | Durum | Mobil Servis | Ekran |
|---|--------------|-------|--------------|-------|
| 18 | POST /auth/refresh | ❌ | auth_service.dart | Token Refresh (YOK) |
| 19 | GET /auth/me | ❌ | auth_service.dart | - |
| 20 | GET /api/predict/food-classes | ❌ | prediction_service.dart (VAR) | Dropdown/Autocomplete |

---

## 📅 GÜN 1: BİLDİRİMLER & BAŞARILAR

**Süre:** 6-7 saat
**Öncelik:** 🔴 KRİTİK (Kullanıcı fark edecek eksiklikler)

### 1.1. notification_service.dart Oluştur

**Dosya Yolu:** `mobile/food_calorie_app/lib/services/notification_service.dart`

**İçerik:**
```dart
import 'api_service.dart';

class NotificationService {
  final ApiService _apiService = ApiService();

  // GET /api/notifications
  Future<Map<String, dynamic>> getNotifications({
    bool? unreadOnly,
    int limit = 50,
    int offset = 0,
  }) async {
    try {
      final response = await _apiService.get('/api/notifications', queryParameters: {
        if (unreadOnly != null) 'unread_only': unreadOnly,
        'limit': limit,
        'offset': offset,
      });
      return response.data;
    } catch (e) {
      throw Exception('Failed to get notifications: $e');
    }
  }

  // GET /api/notifications/unread
  Future<int> getUnreadCount() async {
    try {
      final response = await _apiService.get('/api/notifications/unread');
      return response.data['data']['unread_count'] ?? 0;
    } catch (e) {
      throw Exception('Failed to get unread count: $e');
    }
  }

  // POST /api/notifications/<id>/read
  Future<void> markAsRead(int notificationId) async {
    try {
      await _apiService.post('/api/notifications/$notificationId/read');
    } catch (e) {
      throw Exception('Failed to mark as read: $e');
    }
  }

  // POST /api/notifications/read-all
  Future<int> markAllAsRead() async {
    try {
      final response = await _apiService.post('/api/notifications/read-all');
      return response.data['data']['count'] ?? 0;
    } catch (e) {
      throw Exception('Failed to mark all as read: $e');
    }
  }

  // GET /api/achievements
  Future<List<dynamic>> getAchievements() async {
    try {
      final response = await _apiService.get('/api/achievements');
      return response.data['data']['achievements'] ?? [];
    } catch (e) {
      throw Exception('Failed to get achievements: $e');
    }
  }

  // GET /api/achievements/user
  Future<Map<String, dynamic>> getUserAchievements() async {
    try {
      final response = await _apiService.get('/api/achievements/user');
      return response.data['data'];
    } catch (e) {
      throw Exception('Failed to get user achievements: $e');
    }
  }

  // GET /api/streak
  Future<Map<String, dynamic>> getStreak() async {
    try {
      final response = await _apiService.get('/api/streak');
      return response.data['data'];
    } catch (e) {
      throw Exception('Failed to get streak: $e');
    }
  }

  // GET /api/preferences/notifications
  Future<Map<String, dynamic>> getPreferences() async {
    try {
      final response = await _apiService.get('/api/preferences/notifications');
      return response.data['data'];
    } catch (e) {
      throw Exception('Failed to get preferences: $e');
    }
  }

  // PUT /api/preferences/notifications
  Future<Map<String, dynamic>> updatePreferences(Map<String, dynamic> preferences) async {
    try {
      final response = await _apiService.put('/api/preferences/notifications', data: preferences);
      return response.data['data'];
    } catch (e) {
      throw Exception('Failed to update preferences: $e');
    }
  }
}
```

**Tamamlanma Kriteri:**
- [ ] Dosya oluşturuldu
- [ ] 9 metod tanımlandı
- [ ] Error handling var
- [ ] Try-catch blokları var

---

### 1.2. Notification Model Oluştur

**Dosya Yolu:** `mobile/food_calorie_app/lib/models/notification.dart`

**İçerik:**
```dart
class NotificationModel {
  final int id;
  final String type; // achievement, reminder, weekly_summary, goal_reached, streak
  final String title;
  final String message;
  final Map<String, dynamic>? data;
  final bool isRead;
  final DateTime? readAt;
  final DateTime createdAt;

  NotificationModel({
    required this.id,
    required this.type,
    required this.title,
    required this.message,
    this.data,
    required this.isRead,
    this.readAt,
    required this.createdAt,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      id: json['id'],
      type: json['type'],
      title: json['title'],
      message: json['message'],
      data: json['data'],
      isRead: json['is_read'] ?? false,
      readAt: json['read_at'] != null ? DateTime.parse(json['read_at']) : null,
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  // İkon belirleme helper
  String getIcon() {
    switch (type) {
      case 'achievement':
        return '🏆';
      case 'reminder':
        return '⏰';
      case 'weekly_summary':
        return '📊';
      case 'goal_reached':
        return '🎯';
      case 'streak':
        return '🔥';
      default:
        return '🔔';
    }
  }
}
```

---

### 1.3. Notifications Screen Oluştur

**Dosya Yolu:** `mobile/food_calorie_app/lib/screens/notifications/notifications_screen.dart`

**Özellikler:**
- Bildirim listesi (gruplu: Bugün, Dün, Bu hafta, vb.)
- Okunmamış badge'ler
- Swipe to mark as read
- Pull to refresh
- "Tümünü okundu işaretle" butonu
- Boş state (bildirim yoksa)

**Skeleton Kod:**
```dart
import 'package:flutter/material.dart';
import '../../services/notification_service.dart';
import '../../models/notification.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

class NotificationsScreen extends StatefulWidget {
  @override
  _NotificationsScreenState createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final NotificationService _notificationService = NotificationService();
  List<NotificationModel> _notifications = [];
  bool _isLoading = true;
  int _unreadCount = 0;

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  Future<void> _loadNotifications() async {
    setState(() => _isLoading = true);
    try {
      final data = await _notificationService.getNotifications();
      setState(() {
        _notifications = (data['data']['notifications'] as List)
            .map((json) => NotificationModel.fromJson(json))
            .toList();
        _unreadCount = data['data']['unread_count'] ?? 0;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      // Show error
    }
  }

  Future<void> _markAsRead(int id) async {
    await _notificationService.markAsRead(id);
    _loadNotifications();
  }

  Future<void> _markAllAsRead() async {
    await _notificationService.markAllAsRead();
    _loadNotifications();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.notifications),
        actions: [
          if (_unreadCount > 0)
            TextButton(
              onPressed: _markAllAsRead,
              child: Text(l10n.markAllAsRead),
            ),
        ],
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : _notifications.isEmpty
              ? _buildEmptyState()
              : RefreshIndicator(
                  onRefresh: _loadNotifications,
                  child: ListView.builder(
                    itemCount: _notifications.length,
                    itemBuilder: (context, index) {
                      return _buildNotificationCard(_notifications[index]);
                    },
                  ),
                ),
    );
  }

  Widget _buildNotificationCard(NotificationModel notification) {
    return Dismissible(
      key: Key(notification.id.toString()),
      direction: DismissDirection.endToStart,
      onDismissed: (_) => _markAsRead(notification.id),
      background: Container(
        color: Colors.green,
        alignment: Alignment.centerRight,
        padding: EdgeInsets.only(right: 16),
        child: Icon(Icons.check, color: Colors.white),
      ),
      child: Card(
        margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: ListTile(
          leading: Text(notification.getIcon(), style: TextStyle(fontSize: 32)),
          title: Text(
            notification.title,
            style: TextStyle(
              fontWeight: notification.isRead ? FontWeight.normal : FontWeight.bold,
            ),
          ),
          subtitle: Text(notification.message),
          trailing: notification.isRead
              ? null
              : Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: Theme.of(context).primaryColor,
                    shape: BoxShape.circle,
                  ),
                ),
          onTap: () {
            if (!notification.isRead) {
              _markAsRead(notification.id);
            }
          },
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.notifications_none, size: 80, color: Colors.grey),
          SizedBox(height: 16),
          Text('No notifications yet', style: TextStyle(color: Colors.grey)),
        ],
      ),
    );
  }
}
```

**Tamamlanma Kriteri:**
- [ ] Ekran oluşturuldu
- [ ] Bildirimler listeleniyor
- [ ] Swipe to mark as read çalışıyor
- [ ] Pull to refresh çalışıyor
- [ ] Boş state gösteriliyor

---

### 1.4. Achievements Screen Oluştur

**Dosya Yolu:** `mobile/food_calorie_app/lib/screens/achievements/achievements_screen.dart`

**Özellikler:**
- Tüm başarılar grid view
- Kazanılan rozetler renkli, kazanılmayan gri
- Her rozet için ilerleme çubuğu
- Toplam puan gösterimi
- Rozet detay modal (tıklayınca)

**Backend'den Gelecek Başarılar:**
1. first_prediction - İlk Adım (10 puan)
2. 10_predictions - Başlangıç (20 puan)
3. 100_predictions - Yüzler Kulübü (100 puan)
4. 3_day_streak - Alışkanlık Oluşturma (15 puan)
5. 7_day_streak - Hafta Savaşçısı (30 puan)
6. 30_day_streak - Aylık Usta (100 puan)
7. 7_days_goal - Hedef Tutturucu (50 puan)
8. healthy_week - Sağlıklı Hafta (25 puan)

**Skeleton Kod:**
```dart
import 'package:flutter/material.dart';
import '../../services/notification_service.dart';

class AchievementsScreen extends StatefulWidget {
  @override
  _AchievementsScreenState createState() => _AchievementsScreenState();
}

class _AchievementsScreenState extends State<AchievementsScreen> {
  final NotificationService _notificationService = NotificationService();
  List<dynamic> _allAchievements = [];
  List<dynamic> _userAchievements = [];
  int _totalPoints = 0;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadAchievements();
  }

  Future<void> _loadAchievements() async {
    setState(() => _isLoading = true);
    try {
      final all = await _notificationService.getAchievements();
      final user = await _notificationService.getUserAchievements();

      setState(() {
        _allAchievements = all;
        _userAchievements = user['achievements'] ?? [];
        _totalPoints = user['total_points'] ?? 0;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  bool _hasAchievement(String code) {
    return _userAchievements.any((a) => a['achievement']['code'] == code);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Achievements'),
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : Column(
              children: [
                _buildPointsCard(),
                Expanded(
                  child: GridView.builder(
                    padding: EdgeInsets.all(16),
                    gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 16,
                      mainAxisSpacing: 16,
                    ),
                    itemCount: _allAchievements.length,
                    itemBuilder: (context, index) {
                      final achievement = _allAchievements[index];
                      final earned = _hasAchievement(achievement['code']);
                      return _buildAchievementCard(achievement, earned);
                    },
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildPointsCard() {
    return Container(
      margin: EdgeInsets.all(16),
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.purple, Colors.deepPurple],
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.star, color: Colors.amber, size: 32),
          SizedBox(width: 8),
          Text(
            '$_totalPoints Points',
            style: TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAchievementCard(Map<String, dynamic> achievement, bool earned) {
    return GestureDetector(
      onTap: () => _showAchievementDetail(achievement, earned),
      child: Card(
        elevation: earned ? 4 : 1,
        child: Container(
          padding: EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            color: earned ? null : Colors.grey[200],
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                _getAchievementIcon(achievement['icon']),
                style: TextStyle(
                  fontSize: 48,
                  color: earned ? null : Colors.grey,
                ),
              ),
              SizedBox(height: 8),
              Text(
                achievement['name'],
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: earned ? null : Colors.grey,
                ),
              ),
              SizedBox(height: 4),
              Text(
                '${achievement['points']} pts',
                style: TextStyle(
                  color: earned ? Colors.purple : Colors.grey,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _getAchievementIcon(String icon) {
    // Backend'den icon adı geliyor, emoji'ye çevir
    switch (icon) {
      case 'star':
        return '⭐';
      case 'fire':
        return '🔥';
      case 'trophy':
        return '🏆';
      case 'target':
        return '🎯';
      case 'leaf':
        return '🥗';
      default:
        return '🏅';
    }
  }

  void _showAchievementDetail(Map<String, dynamic> achievement, bool earned) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              _getAchievementIcon(achievement['icon']),
              style: TextStyle(fontSize: 64),
            ),
            SizedBox(height: 16),
            Text(
              achievement['name'],
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              achievement['description'],
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey[600]),
            ),
            SizedBox(height: 16),
            Text(
              '${achievement['points']} Points',
              style: TextStyle(
                fontSize: 20,
                color: Colors.purple,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 16),
            if (earned)
              Container(
                padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.green,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  'Earned! ✓',
                  style: TextStyle(color: Colors.white),
                ),
              )
            else
              Text(
                'Not earned yet',
                style: TextStyle(color: Colors.grey),
              ),
          ],
        ),
      ),
    );
  }
}
```

**Tamamlanma Kriteri:**
- [ ] Ekran oluşturuldu
- [ ] Başarılar grid'de gösteriliyor
- [ ] Kazanılan/kazanılmayan farkı görünüyor
- [ ] Toplam puan gösteriliyor
- [ ] Detay modal çalışıyor

---

### 1.5. Streak Widget Oluştur

**Dosya Yolu:** `mobile/food_calorie_app/lib/widgets/common/streak_widget.dart`

**Özellikler:**
- Mevcut streak sayısı (🔥 7 gün)
- Longest streak
- Milestone gösterimi (3, 7, 14, 30 gün)
- Animasyon (fire emoji)

**Kullanılacağı Yerler:**
- Home Screen (dashboard kartı olarak)
- Profile Screen (stats kısmında)

**Kod:**
```dart
import 'package:flutter/material.dart';
import '../../services/notification_service.dart';

class StreakWidget extends StatefulWidget {
  @override
  _StreakWidgetState createState() => _StreakWidgetState();
}

class _StreakWidgetState extends State<StreakWidget> {
  final NotificationService _notificationService = NotificationService();
  int _currentStreak = 0;
  int _longestStreak = 0;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadStreak();
  }

  Future<void> _loadStreak() async {
    try {
      final data = await _notificationService.getStreak();
      setState(() {
        _currentStreak = data['current_streak'] ?? 0;
        _longestStreak = data['longest_streak'] ?? 0;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Card(
        child: Container(
          height: 100,
          child: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    return Card(
      elevation: 4,
      child: Container(
        padding: EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.orange, Colors.deepOrange],
          ),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Current Streak',
                      style: TextStyle(color: Colors.white70, fontSize: 12),
                    ),
                    SizedBox(height: 4),
                    Row(
                      children: [
                        Text('🔥', style: TextStyle(fontSize: 32)),
                        SizedBox(width: 8),
                        Text(
                          '$_currentStreak',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 32,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        SizedBox(width: 4),
                        Text(
                          'days',
                          style: TextStyle(color: Colors.white, fontSize: 16),
                        ),
                      ],
                    ),
                  ],
                ),
                Column(
                  children: [
                    Text(
                      'Best',
                      style: TextStyle(color: Colors.white70, fontSize: 12),
                    ),
                    SizedBox(height: 4),
                    Text(
                      '$_longestStreak',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            SizedBox(height: 12),
            _buildMilestoneProgress(),
          ],
        ),
      ),
    );
  }

  Widget _buildMilestoneProgress() {
    List<int> milestones = [3, 7, 14, 30];
    int nextMilestone = milestones.firstWhere(
      (m) => m > _currentStreak,
      orElse: () => 30,
    );
    double progress = _currentStreak / nextMilestone;

    return Column(
      children: [
        LinearProgressIndicator(
          value: progress.clamp(0.0, 1.0),
          backgroundColor: Colors.white30,
          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
        ),
        SizedBox(height: 4),
        Text(
          '${nextMilestone - _currentStreak} days to $nextMilestone-day milestone',
          style: TextStyle(color: Colors.white70, fontSize: 11),
        ),
      ],
    );
  }
}
```

**Tamamlanma Kriteri:**
- [ ] Widget oluşturuldu
- [ ] Streak verisi backend'den geliyor
- [ ] Home ve Profile'a eklendi
- [ ] Animasyon var

---

### 1.6. Notification Preferences Screen

**Dosya Yolu:** `mobile/food_calorie_app/lib/screens/settings/notification_preferences_screen.dart`

**Özellikler:**
- Bildirim kanalları (Email, Push, In-App)
- Bildirim tipleri (Başarılar, Hatırlatma, Özet, vb.)
- Hatırlatma saati seçimi
- Kaydetme

**Kod:** (Kısaltılmış)
```dart
class NotificationPreferencesScreen extends StatefulWidget {
  // Switch'ler, TimePicker, Save butonu
  // PUT /api/preferences/notifications ile kaydet
}
```

**Tamamlanma Kriteri:**
- [ ] Ekran oluşturuldu
- [ ] Tercihler backend'den yükleniyor
- [ ] Kaydetme çalışıyor

---

### 1.7. Dil Çevirileri Ekle

**Dosya 1:** `mobile/food_calorie_app/lib/l10n/app_tr.arb`
**Dosya 2:** `mobile/food_calorie_app/lib/l10n/app_en.arb`

**Eklenecek Çeviriler (30+ adet):**
```json
{
  "notifications": "Bildirimler / Notifications",
  "achievements": "Başarılar / Achievements",
  "streak": "Seri / Streak",
  "currentStreak": "Mevcut Seri / Current Streak",
  "longestStreak": "En Uzun Seri / Longest Streak",
  "days": "Gün / Days",
  "markAllAsRead": "Tümünü Okundu İşaretle / Mark All as Read",
  "noNotifications": "Henüz bildirim yok / No notifications yet",
  "totalPoints": "Toplam Puan / Total Points",
  "earned": "Kazanıldı / Earned",
  "notEarnedYet": "Henüz kazanılmadı / Not earned yet",
  "points": "Puan / Points",
  "notificationPreferences": "Bildirim Tercihleri / Notification Preferences",
  "enableEmail": "Email Bildirimleri / Enable Email",
  "enablePush": "Push Bildirimleri / Enable Push",
  "enableInApp": "Uygulama İçi Bildirimler / Enable In-App",
  "notifyAchievements": "Başarı Bildirimleri / Achievement Notifications",
  "notifyDailyReminder": "Günlük Hatırlatma / Daily Reminder",
  "notifyWeeklySummary": "Haftalık Özet / Weekly Summary",
  "notifyGoalReached": "Hedef Başarısı / Goal Reached",
  "notifyStreakMilestone": "Seri Kilometre Taşları / Streak Milestones",
  "dailyReminderTime": "Hatırlatma Saati / Reminder Time",
  "save": "Kaydet / Save",
  "saved": "Kaydedildi / Saved"
}
```

**Tamamlanma Kriteri:**
- [ ] TR çeviriler eklendi
- [ ] EN çeviriler eklendi
- [ ] Tüm ekranlarda kullanıldı

---

### 1.8. Home Screen'e Bildirim Badge Ekle

**Dosya:** `mobile/food_calorie_app/lib/screens/home/home_screen.dart`

**Değişiklik:**
- AppBar'da notification icon'una badge ekle
- Okunmamış sayısını göster
- Tıklandığında Notifications Screen'e git

**Kod Snippet:**
```dart
AppBar(
  actions: [
    Stack(
      children: [
        IconButton(
          icon: Icon(Icons.notifications),
          onPressed: () {
            Navigator.pushNamed(context, '/notifications');
          },
        ),
        if (_unreadCount > 0)
          Positioned(
            right: 8,
            top: 8,
            child: Container(
              padding: EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: Colors.red,
                shape: BoxShape.circle,
              ),
              child: Text(
                '$_unreadCount',
                style: TextStyle(color: Colors.white, fontSize: 10),
              ),
            ),
          ),
      ],
    ),
  ],
)
```

---

### 1.9. Route Eklemeleri

**Dosya:** `mobile/food_calorie_app/lib/main.dart`

**Eklenecek Route'lar:**
```dart
'/notifications': (context) => NotificationsScreen(),
'/achievements': (context) => AchievementsScreen(),
'/notification-preferences': (context) => NotificationPreferencesScreen(),
```

---

### ✅ GÜN 1 TAMAMLANMA KRİTERLERİ

- [ ] notification_service.dart oluşturuldu (9 metod)
- [ ] notification.dart model oluşturuldu
- [ ] NotificationsScreen oluşturuldu ve çalışıyor
- [ ] AchievementsScreen oluşturuldu ve çalışıyor
- [ ] StreakWidget oluşturuldu, Home ve Profile'a eklendi
- [ ] NotificationPreferencesScreen oluşturuldu
- [ ] 30+ dil çevirisi eklendi (TR/EN)
- [ ] Home'da bildirim badge'i çalışıyor
- [ ] 3 yeni route eklendi
- [ ] iOS Simulator'de test edildi

**TEST SENARYOLARI:**
1. Home'dan bildirim ikonuna tıkla → Notifications ekranı açılmalı
2. Bildirimleri listele → Backend'den gelmeli
3. Swipe to mark as read → API çağrısı yapmalı
4. Achievements'e git → 8 rozet görmeli
5. Streak widget'ı → Mevcut streak görünmeli
6. Preferences → Tercihleri değiştir, kaydet

---

## 📅 GÜN 2: HISTORY, PROFILE, STATS

**Süre:** 4-5 saat

### 2.1. History Detail Screen

**Dosya:** `mobile/food_calorie_app/lib/screens/history/history_detail_screen.dart`

**Özellikler:**
- Büyük fotoğraf gösterimi
- Tüm prediction detayları (food, confidence, grams, calories, protein, carbs, fat)
- Mask gösterimi (eğer varsa)
- Meal type badge
- Tarih/saat
- User note
- Edit butonu
- Delete butonu

**API:**
- GET /api/history/<id>

**Kod:** (Skeleton)
```dart
class HistoryDetailScreen extends StatelessWidget {
  final int predictionId;

  HistoryDetailScreen({required this.predictionId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Meal Detail'),
        actions: [
          IconButton(
            icon: Icon(Icons.edit),
            onPressed: () => _editPrediction(context),
          ),
          IconButton(
            icon: Icon(Icons.delete),
            onPressed: () => _deletePrediction(context),
          ),
        ],
      ),
      body: FutureBuilder(
        future: HistoryService().getHistoryDetail(predictionId),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          }

          final prediction = snapshot.data;
          return SingleChildScrollView(
            child: Column(
              children: [
                // Büyük fotoğraf
                Image.network(prediction['image_url']),
                // Detay bilgiler
                _buildDetailCard(prediction),
                // Nutrition info
                _buildNutritionCard(prediction),
              ],
            ),
          );
        },
      ),
    );
  }
}
```

**Tamamlanma Kriteri:**
- [ ] Ekran oluşturuldu
- [ ] Backend'den detay çekiliyor
- [ ] Tüm bilgiler gösteriliyor
- [ ] Edit/Delete butonları var

---

### 2.2. Edit & Delete Fonksiyonları

**Edit Dialog:**
- Meal type değiştirme (dropdown)
- Note güncelleme
- API: PATCH /api/history/<id>

**Delete Confirmation:**
- Confirmation dialog
- API: DELETE /api/history/<id>
- Başarılı silmede History ekranına dön

**history_service.dart'a Eklenecek:**
```dart
// GET /api/history/<id>
Future<Map<String, dynamic>> getHistoryDetail(int id) async {
  try {
    final response = await _apiService.get('/api/history/$id');
    return response.data['data'];
  } catch (e) {
    throw Exception('Failed to get history detail: $e');
  }
}
```

**Tamamlanma Kriteri:**
- [ ] Edit dialog çalışıyor
- [ ] Delete confirmation çalışıyor
- [ ] API çağrıları başarılı

---

### 2.3. Profile Edit Screen

**Dosya:** `mobile/food_calorie_app/lib/screens/profile/edit_profile_screen.dart`

**Mevcut:** UI zaten var ama çalışmıyor

**Yapılacak:**
- Form validation ekle
- PUT /api/user/profile çağrısı ekle
- Success message
- Profile ekranına dön

**auth_service.dart'a Eklenecek:**
```dart
Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> data) async {
  try {
    final response = await _apiService.put('/api/user/profile', data: data);
    return response.data['data'];
  } catch (e) {
    throw Exception('Failed to update profile: $e');
  }
}
```

**Tamamlanma Kriteri:**
- [ ] Form submit çalışıyor
- [ ] Backend'e gönderiliyor
- [ ] Success message gösteriliyor
- [ ] Profile güncellenmiş gösteriliyor

---

### 2.4. Goals Update Screen

**Yeni Dosya:** `mobile/food_calorie_app/lib/screens/profile/goals_screen.dart`

**Özellikler:**
- Günlük kalori hedefi (slider)
- Hedef tipi (lose/maintain/gain weight)
- Aktivite seviyesi (sedentary, light, moderate, active, very active)
- BMR/TDEE otomatik hesaplama ve gösterme
- Save butonu

**API:**
- PUT /api/user/goals

**auth_service.dart'a Eklenecek:**
```dart
Future<Map<String, dynamic>> updateGoals(Map<String, dynamic> data) async {
  try {
    final response = await _apiService.put('/api/user/goals', data: data);
    return response.data['data'];
  } catch (e) {
    throw Exception('Failed to update goals: $e');
  }
}
```

**Tamamlanma Kriteri:**
- [ ] Ekran oluşturuldu
- [ ] Hedef kalori değiştirilebiliyor
- [ ] Backend'e kaydediliyor

---

### 2.5. Stats Top Foods & Favorites

**Dosya:** `mobile/food_calorie_app/lib/screens/stats/stats_screen.dart`

**Mevcut:** Ekran var, hardcoded veriler gösteriyor

**Yapılacak:**
- En çok yenenler listesi (GET /api/stats/top-foods)
- Favori yemekler (GET /api/stats/favorites)
- Güzel kartlar ile gösterim

**stats_service.dart'a Eklenecek:**
```dart
Future<List<dynamic>> getTopFoods({int limit = 5}) async {
  try {
    final response = await _apiService.get('/api/stats/top-foods', queryParameters: {'limit': limit});
    return response.data['data']['top_foods'];
  } catch (e) {
    throw Exception('Failed to get top foods: $e');
  }
}

Future<List<dynamic>> getFavorites() async {
  try {
    final response = await _apiService.get('/api/stats/favorites');
    return response.data['data']['favorites'];
  } catch (e) {
    throw Exception('Failed to get favorites: $e');
  }
}
```

**Stats Screen Değişiklikleri:**
- Top Foods section ekle
- Backend'den veri çek
- Her yemek için: isim, yenme sayısı, toplam kalori

**Tamamlanma Kriteri:**
- [ ] Top Foods backend'den geliyor
- [ ] Favorites gösteriliyor
- [ ] Hardcoded veriler silindi

---

### ✅ GÜN 2 TAMAMLANMA KRİTERLERİ

- [ ] HistoryDetailScreen oluşturuldu
- [ ] Edit dialog çalışıyor
- [ ] Delete confirmation çalışıyor
- [ ] Profile edit çalışıyor
- [ ] Goals screen oluşturuldu
- [ ] Stats top foods eklendi
- [ ] iOS Simulator'de test edildi

**TEST SENARYOLARI:**
1. History'den bir meal'e tıkla → Detay açılmalı
2. Edit butonuna bas → Meal type değiştirebilmeli
3. Delete butonuna bas → Confirmation sonrası silinmeli
4. Profile'da Edit Profile → Bilgileri değiştir, kaydet
5. Goals ekranı → Hedef kalori değiştir
6. Stats → Top foods görmeli

---

## 📅 GÜN 3: DİĞERLERİ + TEST + POLISH

**Süre:** 3-4 saat

### 3.1. Token Refresh Mekanizması

**Dosya:** `mobile/food_calorie_app/lib/services/api_service.dart`

**Mevcut Durum:** 401 alınca kullanıcı logout oluyor

**Değişiklik:**
- 401 alınınca önce token refresh dene
- POST /auth/refresh çağır
- Yeni token al
- Original request'i tekrar yap
- Eğer refresh de başarısız olursa logout

**Kod:**
```dart
class ApiService {
  Dio _dio = Dio();

  ApiService() {
    _dio.interceptors.add(InterceptorsWrapper(
      onError: (DioError e, handler) async {
        if (e.response?.statusCode == 401) {
          // Token expired, try refresh
          try {
            final newToken = await _refreshToken();
            if (newToken != null) {
              // Retry original request
              final options = e.requestOptions;
              options.headers['Authorization'] = 'Bearer $newToken';
              final response = await _dio.request(
                options.path,
                options: Options(
                  method: options.method,
                  headers: options.headers,
                ),
                data: options.data,
                queryParameters: options.queryParameters,
              );
              return handler.resolve(response);
            }
          } catch (_) {
            // Refresh failed, logout
            await clearToken();
            // Navigate to login
          }
        }
        return handler.next(e);
      },
    ));
  }

  Future<String?> _refreshToken() async {
    try {
      final response = await _dio.post('/auth/refresh');
      final newToken = response.data['data']['access_token'];
      await saveToken(newToken);
      return newToken;
    } catch (e) {
      return null;
    }
  }
}
```

**Tamamlanma Kriteri:**
- [ ] 401 interceptor eklendi
- [ ] Token refresh çalışıyor
- [ ] Retry mekanizması var

---

### 3.2. Food Classes Listesi

**API:** GET /api/predict/food-classes

**Kullanım Alanı:**
- Dropdown/autocomplete olarak kullanılabilir (gelecekte)
- Şimdilik sadece backend'den çekelim

**prediction_service.dart'ta Zaten Var:**
```dart
Future<Map<String, dynamic>> getFoodClasses() async {
  // Zaten var, test et
}
```

**Tamamlanma Kriteri:**
- [ ] API çağrısı test edildi
- [ ] Veri geliyor

---

### 3.3. Tüm Ekranları Test Et

**iOS Simulator Test Checklist:**

**Authentication:**
- [ ] Login çalışıyor
- [ ] Register çalışıyor
- [ ] Auto-login çalışıyor
- [ ] Logout çalışıyor

**Home:**
- [ ] Dashboard gösteriliyor
- [ ] Bildirim badge sayısı doğru
- [ ] Streak widget görünüyor
- [ ] Quick actions çalışıyor

**Camera & Prediction:**
- [ ] Kamera açılıyor
- [ ] Galeri seçiliyor
- [ ] AI prediction çalışıyor
- [ ] Result gösteriliyor
- [ ] Geçmişe kaydediyor

**History:**
- [ ] Liste gösteriliyor
- [ ] Detaya tıklayınca açılıyor
- [ ] Edit çalışıyor
- [ ] Delete çalışıyor

**Stats:**
- [ ] Günlük özet doğru
- [ ] Grafikler gösteriliyor
- [ ] Top foods gösteriliyor
- [ ] Meal distribution doğru

**Profile:**
- [ ] Profil gösteriliyor
- [ ] Edit profile çalışıyor
- [ ] Goals değiştirilebiliyor
- [ ] Streak gösteriliyor

**Notifications:**
- [ ] Bildirimler listeleniyor
- [ ] Mark as read çalışıyor
- [ ] Badge güncellenmiyor

**Achievements:**
- [ ] Rozetler gösteriliyor
- [ ] Kazanılan/kazanılmayan farkı var
- [ ] Detay modal çalışıyor
- [ ] Puan toplam doğru

**Settings:**
- [ ] Notification preferences çalışıyor
- [ ] Dil değiştirme çalışıyor

---

### 3.4. Bug Fix & Polish

**Yapılacaklar:**

1. **Animasyonlar Ekle:**
   - Ekran geçişleri (fade, slide)
   - Loading shimmer (skeleton screen)
   - Success animations (Lottie)

2. **Loading States:**
   - Shimmer placeholders
   - Skeleton screens
   - Progress indicators

3. **Error Handling:**
   - User-friendly error messages
   - Retry butonları
   - Offline mode mesajları

4. **Toast Messages:**
   - Success: "Saved!", "Deleted!", "Marked as read!"
   - Error: "Something went wrong", "Network error"
   - Info: "Loading..."

5. **UI Polish:**
   - Tutarlı spacing
   - Color scheme finalize
   - Font sizes standart
   - Icon consistency

---

### 3.5. Final Review

**Kod Temizliği:**
- [ ] Unused imports temizle
- [ ] Console.log/print'ler sil
- [ ] TODO comment'leri kontrol et
- [ ] Kod formatla (dart format)

**Dokümantasyon:**
- [ ] README güncelle
- [ ] API endpoint listesi güncelle
- [ ] Ekran listesi güncelle

**Git Commit:**
```bash
git add .
git commit -m "feat: Tüm backend API'leri mobil uygulamaya entegre edildi

✅ Bildirimler & Başarılar
- Notifications screen
- Achievements screen
- Streak widget
- Notification preferences

✅ History CRUD
- History detail screen
- Edit/Delete fonksiyonları

✅ Profile & Goals
- Profile edit çalışıyor
- Goals update screen

✅ Stats Tamamlama
- Top foods
- Favorites

✅ Diğer
- Token refresh
- Food classes
- 50+ dil çevirisi

🎉 Backend: 31/31 endpoint entegre
🎉 Mobil: %100 tamamlandı

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### ✅ GÜN 3 TAMAMLANMA KRİTERLERİ

- [ ] Token refresh çalışıyor
- [ ] Food classes test edildi
- [ ] Tüm ekranlar test edildi
- [ ] Bug'lar düzeltildi
- [ ] Animasyonlar eklendi
- [ ] Error handling iyileştirildi
- [ ] Kod temizlendi
- [ ] Git commit atıldı

---

## 📊 GENEL TAMAMLANMA KRİTERLERİ

### Backend API Entegrasyonu (23 API)

**Grup 1: Notifications & Achievements (10/10):**
- [ ] GET /api/notifications
- [ ] GET /api/notifications/unread
- [ ] POST /api/notifications/<id>/read
- [ ] POST /api/notifications/read-all
- [ ] GET /api/achievements
- [ ] GET /api/achievements/user
- [ ] GET /api/streak
- [ ] GET /api/preferences/notifications
- [ ] PUT /api/preferences/notifications

**Grup 2: History (3/3):**
- [ ] GET /api/history/<id>
- [ ] PATCH /api/history/<id>
- [ ] DELETE /api/history/<id>

**Grup 3: Stats (2/2):**
- [ ] GET /api/stats/top-foods
- [ ] GET /api/stats/favorites

**Grup 4: Profile (2/2):**
- [ ] PUT /api/user/profile
- [ ] PUT /api/user/goals

**Grup 5: Diğer (3/3):**
- [ ] POST /auth/refresh
- [ ] GET /auth/me
- [ ] GET /api/predict/food-classes

**TOPLAM: 20/23 API (3 tanesi opsiyonel)**

---

### Yeni Ekranlar (6 Ekran)

- [ ] Notifications Screen
- [ ] Achievements Screen
- [ ] History Detail Screen
- [ ] Notification Preferences Screen
- [ ] Goals Screen
- [ ] (Edit Profile zaten var, düzeltildi)

---

### Yeni Servisler (1 Yeni Servis)

- [ ] notification_service.dart (9 metod)

---

### Yeni Modeller (1 Model)

- [ ] notification.dart

---

### Yeni Widget'lar (1 Widget)

- [ ] StreakWidget

---

### Dil Çevirileri (50+ Çeviri)

- [ ] Türkçe (TR) - 50+ yeni çeviri
- [ ] İngilizce (EN) - 50+ yeni çeviri

---

## 🎯 SON DURUM (3 Gün Sonrası)

| Metrik | Öncesi | Sonrası |
|--------|--------|---------|
| **Backend API Kullanımı** | 7/31 (%23) | 30/31 (%97) |
| **Mobil Ekran** | 10 ekran | 16 ekran |
| **Servis Dosyası** | 5 servis | 6 servis |
| **Kod Satırı** | ~2,622 | ~4,200 |
| **Dil Çevirisi** | ~150 | ~200 |
| **Mobil Tamamlanma** | %70 | %100 ✅ |

---

## 📝 NOTLAR

### Önemli Hatırlatmalar

1. **Her gün sonunda test et!** - iOS Simulator'de çalıştır, bug'ları hemen gör.

2. **Dil çevirilerini unutma!** - Her yeni ekran için TR/EN ekle.

3. **Error handling ekle!** - Try-catch, user-friendly mesajlar.

4. **Loading states ekle!** - CircularProgressIndicator, shimmer.

5. **Git commit düzenli at!** - Her major özellik sonrası commit.

### Karşılaşılabilecek Sorunlar

**Problem 1: Backend response format farklı**
- **Çözüm:** console.log ile backend response'u kontrol et, model'i düzelt

**Problem 2: Null safety hataları**
- **Çözüm:** `?.` ve `??` operatörlerini kullan, nullable field'lara dikkat et

**Problem 3: 401 Unauthorized**
- **Çözüm:** Token'ı kontrol et, refresh mekanizması çalışıyor mu?

**Problem 4: Image yüklenmiyor**
- **Çözüm:** Base URL doğru mu? CORS ayarları backend'de var mı?

### Test Kullanıcısı

- **Email:** filigoz@example.com
- **Şifre:** test123

### Backend URL

- **Development:** http://localhost:5001
- **Mobil constants.dart:** baseUrl = 'http://localhost:5001'

---

## 🚀 BAŞLAMA KOMUTU

3 gün sonra bu raporu okuyup devam edecek kişi (Claude veya ben):

1. Bu dosyayı oku: `HAFTA_9_PLAN_DETAYLI.md`
2. TODO listesini kontrol et
3. Nerede kaldığını gör (completed/pending)
4. Kaldığın yerden devam et
5. Her tamamlanan işi işaretle
6. Test et, commit at

**İlk iş:** GÜN 1, Adım 1.1 - `notification_service.dart` oluştur

---

**Hazırlayan:** Claude Code
**Tarih:** 20 Aralık 2025
**Tahmini Süre:** 3 gün (15-18 saat)
**Tamamlanma Beklentisi:** %100 backend entegrasyonu ✅
