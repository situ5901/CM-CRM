from pymongo import MongoClient
import requests
import time
from datetime import datetime
import sys

# Update MongoDB connection setup
try:
    client = MongoClient("mongodb+srv://ceo:m1jZaiWN2ulUH0ux@cluster1.zdfza.mongodb.net/")
    db = client['test']
    # Test connection
    client.admin.command('ping')
    print("MongoDB connection successful!")
except Exception as e:
    print(f"MongoDB connection failed: {str(e)}")
    raise

mis_collection = db['mis']

def get_partners_for_phones(phones):
    """Call getPartners API with a batch of phone numbers"""
    api_url = "https://credmantra.com/api/v1/crm/getPartners"
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(
            api_url,
            json={"phones": phones},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API request failed with status code {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling API: {str(e)}")
        return None

def save_history_entry(start_time, end_time=None, status="RUNNING", records_processed=0, error_message=None):
    try:
        history_collection = db.loop_history
        
        entry = {
            'start_time': start_time,
            'end_time': end_time,
            'status': status,
            'records_processed': records_processed,
            'error_message': error_message,
            'created_at': datetime.now()
        }
        
        result = history_collection.insert_one(entry)
        print(f"History entry saved with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"Error saving history entry: {str(e)}")
        return None

def update_status(processed, total, message, batch_info=None):
    try:
        history_collection = db.loop_history
        status_update = {
            'records_processed': processed,
            'message': message,
            'total_records': total,
        }
        
        if batch_info:
            status_update.update({
                'currentBatch': batch_info.get('currentBatch', 0),
                'batchSuccess': batch_info.get('batchSuccess', 0),
                'batchFailed': batch_info.get('batchFailed', 0),
                'batchLog': batch_info.get('batchLog', '')
            })
        
        history_collection.update_one(
            {'status': 'RUNNING'},
            {'$set': status_update}
        )
    except Exception as e:
        print(f"Error updating status: {str(e)}")

def main():
    # Get batch size and delay from command line arguments
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    delay_time = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    start_time = datetime.now()
    save_history_entry(start_time)
    
    try:
        # Find documents without partner key
        query = {
            "$or": [
                {"partner": {"$exists": False}},
                {"partner": None},
                {"partner": ""},
                {"partner": "unknown"},
                {"partner": "Unknown"}
            ]
        }
        total_docs = mis_collection.count_documents(query)
        
        if total_docs == 0:
            print("No documents found without 'partner' key")
            return
        
        print(f"Found {total_docs} documents without 'partner' key")
        
        processed = 0
        failed = 0
        
        # Update the batch processing with status updates
        cursor = mis_collection.find(query, {"phone": 1})
        current_batch = []
        batch_number = 0
        batch_success = 0
        batch_failed = 0
        
        for doc in cursor:
            if "phone" not in doc:
                continue
            
            current_batch.append(doc["phone"])
            
            if len(current_batch) >= batch_size or processed + len(current_batch) == total_docs:
                batch_number += 1
                batch_info = {
                    'currentBatch': batch_number,
                    'batchSuccess': batch_success,
                    'batchFailed': batch_failed,
                    'batchLog': f"Processing batch {batch_number} with {len(current_batch)} phones"
                }
                
                update_status(processed, total_docs, 
                    f"Processing batch {processed+1}-{processed+len(current_batch)}", 
                    batch_info)
                
                # Get partner data for current batch
                partner_data = get_partners_for_phones(current_batch)
                batch_success_count = 0
                batch_failed_count = 0
                
                if partner_data:
                    # Update documents with partner info
                    for item in partner_data:
                        if isinstance(item, dict) and "phone" in item and "partner" in item:
                            try:
                                #### Print document before update
                                # doc_before = mis_collection.find_one({"phone": item["phone"]})
                                # print(f"\nBefore update: {doc_before}")
                                result = mis_collection.update_many(  # Changed to update_many
                                    {"phone": item["phone"]},
                                    {
                                        "$set": {
                                            "partner": item["partner"],
                                            "updatedAt": datetime.now(),
                                            "ref": {"name": "partnerloop", "time": datetime.now()}
                                        }
                                    }
                                )

                                # print(item["partner"])
                                if result.modified_count > 0:
                                    batch_success_count += 1
                                    print(f"Updated {result.modified_count} documents for phone: {item['phone']}")
                                else:
                                    print(f"No update needed for phone: {item['phone']}")
                            except Exception as e:
                                print(f"Error updating documents for phone {item['phone']}: {str(e)}")
                                batch_failed_count += 1
                else:
                    batch_failed_count += len(current_batch)
                
                batch_success += batch_success_count
                batch_failed += batch_failed_count
                
                # Update status with batch results
                batch_info['batchSuccess'] = batch_success
                batch_info['batchFailed'] = batch_failed
                batch_info['batchLog'] = (
                    f"Batch {batch_number} completed: "
                    f"{batch_success_count} successful, "
                    f"{batch_failed_count} failed"
                )
                
                update_status(processed + len(current_batch), total_docs,
                    f"Completed batch {batch_number}", batch_info)
                
                processed += len(current_batch)
                print(f"Progress: {processed}/{total_docs} documents processed ({failed} failed)")
                
                # Clear batch
                current_batch = []
                
                # Add delay to avoid overwhelming the API
                time.sleep(delay_time)
        
        end_time = datetime.now()
        save_history_entry(
            start_time, 
            end_time, 
            "SUCCESS", 
            processed, 
            f"Completed with {failed} failures"
        )
        
    except Exception as e:
        end_time = datetime.now()
        save_history_entry(start_time, end_time, "ERROR", processed, str(e))
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print(f"Script error: {str(e)}")
    finally:
        client.close() 