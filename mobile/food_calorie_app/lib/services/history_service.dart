import 'package:dio/dio.dart';
import '../config/constants.dart';
import '../models/prediction.dart';
import '../models/daily_stats.dart';
import 'api_service.dart';

class HistoryService {
  final ApiService _apiService = ApiService();

  Future<Map<String, dynamic>> getHistory({int page = 1, int limit = 20}) async {
    try {
      final response = await _apiService.get(
        AppConstants.historyEndpoint,
        queryParameters: {'page': page, 'per_page': limit},
      );

      if (response.statusCode == 200) {
        final data = response.data['data'] ?? response.data;
        final List<Prediction> predictions = (data['predictions'] as List)
            .map((item) => Prediction.fromJson(item))
            .toList();

        final pagination = data['pagination'] ?? {};
        return {
          'success': true,
          'predictions': predictions,
          'total': pagination['total_items'] ?? predictions.length,
          'page': pagination['page'] ?? page,
          'pages': pagination['total_pages'] ?? 1,
        };
      } else {
        return {
          'success': false,
          'message': 'Failed to fetch history',
        };
      }
    } on DioException catch (e) {
      return {
        'success': false,
        'message': e.response?.data['message'] ?? 'Network error',
      };
    } catch (e) {
      return {
        'success': false,
        'message': 'An unexpected error occurred',
      };
    }
  }

  Future<Map<String, dynamic>> getDailyStats(String date) async {
    try {
      final response = await _apiService.get(
        AppConstants.dailyLogEndpoint,
        queryParameters: {'date': date},
      );

      if (response.statusCode == 200) {
        final data = response.data['data'] ?? response.data;
        return {
          'success': true,
          'stats': DailyStats.fromJson(data),
        };
      } else {
        return {
          'success': false,
          'message': 'Failed to fetch daily stats',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'message': 'An error occurred',
      };
    }
  }

  Future<Map<String, dynamic>> updatePrediction(
    int id, {
    String? mealType,
    String? userNote,
    bool? isFavorite,
  }) async {
    try {
      final data = <String, dynamic>{};
      if (mealType != null) data['meal_type'] = mealType;
      if (userNote != null) data['user_note'] = userNote;
      if (isFavorite != null) data['is_favorite'] = isFavorite;

      final response = await _apiService.patch(
        '${AppConstants.historyEndpoint}/$id',
        data: data,
      );

      if (response.statusCode == 200) {
        return {
          'success': true,
          'prediction': Prediction.fromJson(response.data['data']),
        };
      } else {
        return {
          'success': false,
          'message': 'Failed to update prediction',
        };
      }
    } on DioException catch (e) {
      return {
        'success': false,
        'message': e.response?.data['error'] ?? 'Network error',
      };
    } catch (e) {
      return {
        'success': false,
        'message': 'An unexpected error occurred',
      };
    }
  }

  Future<Map<String, dynamic>> deletePrediction(int id) async {
    try {
      final response = await _apiService.delete('${AppConstants.historyEndpoint}/$id');

      if (response.statusCode == 200) {
        return {'success': true};
      } else {
        return {
          'success': false,
          'message': 'Failed to delete prediction',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'message': 'An error occurred',
      };
    }
  }

  Future<Map<String, dynamic>> getHistoryDetail(int id) async {
    try {
      final response = await _apiService.get('${AppConstants.historyEndpoint}/$id');
      if (response.statusCode == 200) {
        final data = response.data['data'] ?? response.data;
        return {'success': true, 'prediction': Prediction.fromJson(data)};
      }
      return {'success': false, 'message': 'Failed to fetch history detail'};
    } on DioException catch (e) {
      return {'success': false, 'message': e.response?.data['message'] ?? 'Network error'};
    } catch (e) {
      return {'success': false, 'message': 'An unexpected error occurred'};
    }
  }
}
