import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:food_calorie_app/generated/app_localizations.dart';
import '../../config/theme.dart';
import '../../services/stats_service.dart';
import 'package:intl/intl.dart';

class StatsScreen extends StatefulWidget {
  const StatsScreen({super.key});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> {
  final StatsService _statsService = StatsService();
  String _selectedPeriod = 'week';
  bool _isLoading = true;

  // Backend data
  Map<String, dynamic>? _dailyData;
  List<dynamic>? _weeklyData;
  List<dynamic>? _monthlyData;
  Map<String, dynamic>? _mealDistribution;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
    });

    try {
      // Load all data in parallel
      final results = await Future.wait([
        _statsService.getDailyLog(),
        _statsService.getWeeklyLog(),
        _statsService.getMonthlyLog(),
        _statsService.getMealDistribution(),
      ]);

      if (mounted) {
        setState(() {
          if (results[0]['success'] == true) {
            _dailyData = results[0]['data'];
            print('DEBUG: Daily data = $_dailyData');
          }
          if (results[1]['success'] == true) {
            _weeklyData = results[1]['data'];
            print('DEBUG: Weekly data length = ${_weeklyData?.length}');
          }
          if (results[2]['success'] == true) {
            _monthlyData = results[2]['data'];
            print('DEBUG: Monthly data length = ${_monthlyData?.length}');
          }
          if (results[3]['success'] == true) {
            _mealDistribution = results[3]['data'];
            print('DEBUG: Meal distribution = $_mealDistribution');
          }
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.stats),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildPeriodSelector(),
                  const SizedBox(height: 24),
                  _buildTodaySummary(),
                  const SizedBox(height: 24),
                  _buildCaloriesChart(),
                  const SizedBox(height: 24),
                  _buildMacrosChart(),
                  const SizedBox(height: 24),
                  _buildMealDistribution(),
                ],
              ),
            ),
    );
  }

  Widget _buildPeriodSelector() {
    final l10n = AppLocalizations.of(context)!;
    final periods = {
      'week': l10n.week,
      'month': l10n.month,
      'year': l10n.year,
    };

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Row(
          children: periods.entries.map((entry) {
            final isSelected = _selectedPeriod == entry.key;
            return Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4.0),
                child: ElevatedButton(
                  onPressed: () {
                    setState(() {
                      _selectedPeriod = entry.key;
                    });
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isSelected
                        ? AppTheme.primaryColor
                        : Colors.grey.shade200,
                    foregroundColor:
                        isSelected ? Colors.white : AppTheme.textPrimaryColor,
                    elevation: isSelected ? 2 : 0,
                  ),
                  child: Text(entry.value),
                ),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildTodaySummary() {
    final l10n = AppLocalizations.of(context)!;

    // Get data from backend or use defaults
    final calories = ((_dailyData?['total_calories'] ?? 0) as num).toInt();
    final protein = ((_dailyData?['protein'] ?? 0) as num).toInt();
    final carbs = ((_dailyData?['carbs'] ?? 0) as num).toInt();
    final fat = ((_dailyData?['fat'] ?? 0) as num).toInt();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.todaySummary,
              style: Theme.of(context).textTheme.displayMedium,
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildSummaryItem(l10n.calories, calories.toString(), l10n.kcal, AppTheme.accentColor),
                _buildSummaryItem(l10n.protein, protein.toString(), l10n.grams, Colors.blue),
                _buildSummaryItem(l10n.carbs, carbs.toString(), l10n.grams, Colors.orange),
                _buildSummaryItem(l10n.fat, fat.toString(), l10n.grams, Colors.amber),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryItem(String label, String value, String unit, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          unit,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey.shade600,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: 14,
            color: AppTheme.textSecondaryColor,
          ),
        ),
      ],
    );
  }

  Widget _buildCaloriesChart() {
    final l10n = AppLocalizations.of(context)!;

    final chartData = _getChartData(l10n);
    final spots = chartData.spots;
    final xLabels = chartData.xLabels;
    // Y ekseni: varsayılan 0-3K; daha yüksekse %10 baş boşluğu ile genişlet
    double maxY = chartData.maxY > 0 ? chartData.maxY * 1.1 : 3000;
    if (maxY < 3000) maxY = 3000;
    // Gösterilecek sabit tick’ler (0, 1K, 2K, 3K) + gerekirse maxY
    final tickValues = <double>[0, 1000, 2000, 3000];
    if (maxY > 3000) {
      tickValues.add(maxY.roundToDouble());
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _selectedPeriod == 'week'
                  ? 'Bu Haftanın Kalorileri'
                  : _selectedPeriod == 'month'
                      ? '${_currentMonthName()} Ayı Kalorileri'
                      : '${DateTime.now().year} Yılı Kalorileri',
              style: Theme.of(context).textTheme.displayMedium,
            ),
            const SizedBox(height: 24),
            SizedBox(
              height: 220,
              child: LineChart(
                LineChartData(
                  gridData: FlGridData(show: false),
                  titlesData: FlTitlesData(
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 40,
                        getTitlesWidget: (value, meta) {
                          // Tick'leri sabit listeden göster
                          const eps = 0.01;
                          final hit = tickValues.any((t) => (t - value).abs() < eps);
                          if (hit) {
                            if (value >= 1000) {
                              return Text('${(value / 1000).toStringAsFixed(0)}K');
                            }
                            return Text(value.toInt().toString());
                          }
                          return const SizedBox.shrink();
                        },
                      ),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          final idx = value.toInt();
                          if (idx >= 0 && idx < xLabels.length) {
                            return Text(xLabels[idx], style: const TextStyle(fontSize: 10));
                          }
                          return const Text('');
                        },
                      ),
                    ),
                    topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  ),
                  borderData: FlBorderData(show: false),
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      isCurved: true,
                      color: AppTheme.primaryColor,
                      barWidth: 3,
                      dotData: FlDotData(show: true),
                      belowBarData: BarAreaData(
                        show: true,
                        color: AppTheme.primaryColor.withOpacity(0.1),
                      ),
                    ),
                  ],
                  minY: 0,
                  maxY: maxY,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMacrosChart() {
    final l10n = AppLocalizations.of(context)!;

    // Get data from backend or use defaults
    final protein = ((_dailyData?['protein'] ?? 0) as num).toDouble();
    final carbs = ((_dailyData?['carbs'] ?? 0) as num).toDouble();
    final fat = ((_dailyData?['fat'] ?? 0) as num).toDouble();

    // Calculate calories from macros (protein/carbs = 4 cal/g, fat = 9 cal/g)
    final proteinCals = protein * 4;
    final carbsCals = carbs * 4;
    final fatCals = fat * 9;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.macronutrientsToday,
              style: Theme.of(context).textTheme.displayMedium,
            ),
            const SizedBox(height: 24),
            SizedBox(
              height: 200,
              child: PieChart(
                PieChartData(
                  sectionsSpace: 2,
                  centerSpaceRadius: 60,
                  sections: [
                    PieChartSectionData(
                      value: proteinCals,
                      title: '${l10n.protein}\n${protein.toInt()}g',
                      color: Colors.blue,
                      radius: 50,
                      titleStyle: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    PieChartSectionData(
                      value: carbsCals,
                      title: '${l10n.carbs}\n${carbs.toInt()}g',
                      color: Colors.orange,
                      radius: 50,
                      titleStyle: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    PieChartSectionData(
                      value: fatCals,
                      title: '${l10n.fat}\n${fat.toInt()}g',
                      color: Colors.amber,
                      radius: 50,
                      titleStyle: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMealDistribution() {
    final l10n = AppLocalizations.of(context)!;

    // Get data from backend or use defaults
    final distribution = _mealDistribution?['distribution'] as Map<String, dynamic>?;
    final breakfastCals = ((distribution?['breakfast']?['total_calories'] ?? 0) as num).toDouble();
    final lunchCals = ((distribution?['lunch']?['total_calories'] ?? 0) as num).toDouble();
    final dinnerCals = ((distribution?['dinner']?['total_calories'] ?? 0) as num).toDouble();
    final snackCals = ((distribution?['snack']?['total_calories'] ?? 0) as num).toDouble();
    final totalCals = ((_dailyData?['total_calories'] ?? 2000) as num).toDouble();
    final maxCalories = totalCals > 0 ? totalCals : 2000.0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.mealDistribution,
              style: Theme.of(context).textTheme.displayMedium,
            ),
            const SizedBox(height: 16),
            _buildMealBar(l10n.breakfast, breakfastCals, maxCalories, Colors.orange),
            const SizedBox(height: 12),
            _buildMealBar(l10n.lunch, lunchCals, maxCalories, AppTheme.secondaryColor),
            const SizedBox(height: 12),
            _buildMealBar(l10n.dinner, dinnerCals, maxCalories, AppTheme.primaryColor),
            const SizedBox(height: 12),
            _buildMealBar(l10n.snack, snackCals, maxCalories, Colors.purple),
          ],
        ),
      ),
    );
  }

  Widget _buildMealBar(String label, double calories, double maxCalories, Color color) {
    final l10n = AppLocalizations.of(context)!;
    final percentage = (calories / maxCalories).clamp(0.0, 1.0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(
              '${calories.toStringAsFixed(0)} ${l10n.kcal}',
              style: TextStyle(color: color, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        const SizedBox(height: 8),
        LinearProgressIndicator(
          value: percentage,
          backgroundColor: Colors.grey.shade200,
          color: color,
          minHeight: 8,
          borderRadius: BorderRadius.circular(4),
        ),
      ],
    );
  }

  _ChartData _getChartData(AppLocalizations l10n) {
    if (_selectedPeriod == 'month') {
      final data = _monthlyData ?? [];
      data.sort((a, b) => (a['date'] ?? '').compareTo(b['date'] ?? ''));
      // Bu ay: 4 veya 5 haftaya böler (gün sayısına göre)
      int weekCount = ((data.length + 6) ~/ 7);
      if (weekCount < 4) weekCount = 4;
      if (weekCount > 5) weekCount = 5;
      final chunkSize = (data.isEmpty ? 0 : (data.length / weekCount).ceil()).clamp(1, 7);
      final spots = <FlSpot>[];
      final labels = <String>[];
      double maxY = 0;
      int bucketIndex = 0;
      for (int i = 0; i < data.length; i += chunkSize) {
        final chunk = data.sublist(i, i + chunkSize > data.length ? data.length : i + chunkSize);
        if (chunk.isEmpty) continue;
        final caloriesSum = chunk.fold<num>(
          0,
          (sum, e) => sum + ((e['total_calories'] ?? 0) as num),
        );
        // Haftalık ortalama istendiği için gün sayısına bölelim
        final y = (caloriesSum / chunk.length).toDouble();
        maxY = y > maxY ? y : maxY;
        spots.add(FlSpot(bucketIndex.toDouble(), y));
        labels.add('H${bucketIndex + 1}');
        bucketIndex++;
      }
      if (spots.isEmpty) {
        // Veri yoksa yine de weekCount kadar 0 nokta üret
        for (int i = 0; i < weekCount; i++) {
          spots.add(FlSpot(i.toDouble(), 0));
          labels.add('H${i + 1}');
        }
      }
      return _ChartData(spots: spots, xLabels: labels, maxY: maxY);
    }

    if (_selectedPeriod == 'year') {
      // 12 ay (Ocak-Aralık) toplam kalori
      final data = _monthlyData ?? [];
      final monthTotals = List<double>.filled(12, 0);
      for (final e in data) {
        final dateStr = e['date'];
        if (dateStr is String && dateStr.isNotEmpty) {
          final dt = DateTime.tryParse(dateStr);
          if (dt != null) {
            monthTotals[dt.month - 1] += ((e['total_calories'] ?? 0) as num).toDouble();
          }
        }
      }
      final labels = <String>['O', 'Ş', 'M', 'N', 'M', 'H', 'T', 'A', 'E', 'E', 'K', 'A'];
      final spots = <FlSpot>[];
      double maxY = 0;
      for (int i = 0; i < 12; i++) {
        final y = monthTotals[i];
        maxY = y > maxY ? y : maxY;
        spots.add(FlSpot(i.toDouble(), y));
      }
      return _ChartData(spots: spots, xLabels: labels, maxY: maxY);
    }

    // Week (default)
    final data = _weeklyData ?? [];
    data.sort((a, b) => (a['date'] ?? '').compareTo(b['date'] ?? ''));
    final labels = <String>[];
    final spots = <FlSpot>[];
    double maxY = 0;
    for (int i = 0; i < data.length; i++) {
      final e = data[i];
      final calories = ((e['total_calories'] ?? 0) as num).toDouble();
      maxY = calories > maxY ? calories : maxY;
      String label = '';
      final dateStr = e['date'];
      if (dateStr is String && dateStr.isNotEmpty) {
        final dt = DateTime.tryParse(dateStr);
        if (dt != null) {
          label = _weekdayLabel(dt.weekday, l10n);
        }
      }
      labels.add(label);
      spots.add(FlSpot(i.toDouble(), calories));
    }
    // Eğer veri gelmezse sabit 7 gün boş grafik
    if (spots.isEmpty) {
      final defaultLabels = [l10n.mon, l10n.tue, l10n.wed, l10n.thu, l10n.fri, l10n.sat, l10n.sun];
      for (int i = 0; i < defaultLabels.length; i++) {
        labels.add(defaultLabels[i]);
        spots.add(FlSpot(i.toDouble(), 0));
      }
    }
    return _ChartData(spots: spots, xLabels: labels, maxY: maxY);
  }

  String _currentMonthName() {
    final now = DateTime.now();
    const months = [
      'Ocak',
      'Şubat',
      'Mart',
      'Nisan',
      'Mayıs',
      'Haziran',
      'Temmuz',
      'Ağustos',
      'Eylül',
      'Ekim',
      'Kasım',
      'Aralık'
    ];
    return months[now.month - 1];
  }

  String _weekdayLabel(int weekday, AppLocalizations l10n) {
    switch (weekday) {
      case DateTime.monday:
        return l10n.mon;
      case DateTime.tuesday:
        return l10n.tue;
      case DateTime.wednesday:
        return l10n.wed;
      case DateTime.thursday:
        return l10n.thu;
      case DateTime.friday:
        return l10n.fri;
      case DateTime.saturday:
        return l10n.sat;
      case DateTime.sunday:
        return l10n.sun;
      default:
        return '';
    }
  }
}

class _ChartData {
  final List<FlSpot> spots;
  final List<String> xLabels;
  final double maxY;

  _ChartData({
    required this.spots,
    required this.xLabels,
    required this.maxY,
  });
}
